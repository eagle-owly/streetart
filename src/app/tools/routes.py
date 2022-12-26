from flask import request, render_template, send_file
from . import tools

import base64
import numpy as np
from PIL import Image
from io import BytesIO
from itertools import groupby
from sklearn.cluster import DBSCAN

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

from .aco import Aco
from .spray_cans import spray_cans

box_dimension = 400
color_merge_tolerance = 3
smallest_area_ratio = 0.001


@tools.route('/color_calc', methods=['GET', 'POST'])
def color_calc():
    if 'image' in request.files:
        width = float(request.form.get('width'))
        height = float(request.form.get('height'))
        m2_per_can = float(request.form.get('m2_per_can'))
        layers = float(request.form.get('layers'))

        area = width * height
        cans = (layers * area) / m2_per_can

        base64_img, results = calculate_colors(request.files.get('image'))
        painting_info = []

        for color, (area_pct, bg_color, text_color) in results:
            color = np.array(color)
            distances = [compare_colors(color, np.array(can[0])) for can in spray_cans]

            best_can = spray_cans[np.argmin(distances)]
            cans_needed = round(area_pct * cans / 100, 1)
            color_area_m2 = round(area_pct * area / 100, 2)

            painting_info.append((best_can[1], best_can[2], cans_needed, color_area_m2))

        results = list(zip(results, painting_info))
        results_grouped = []

        for color, data in groupby(results, key=lambda x: (x[1][0], x[1][1])):
            data = list(data)

            found_colors = [dict(zip(['area_pct', 'bg_color', 'txt_color'], x[0][1])) for x in data]
            n_cans = round(sum([x[1][2] for x in data]), 1)
            area_m2 = round(sum([x[1][3] for x in data]), 2)
            area_pct = round(sum([x[0][1][0] for x in data]), 1)

            results_grouped.append({'spray_rgb': color[0], 'spray_name': color[1], 'found_colors': found_colors,
                                    'n_cans': n_cans, 'area_m2': area_m2, 'area_pct': area_pct})

        return render_template('tools.html', results=results_grouped, base64_img=base64_img,
                               total_area=round(area, 2),
                               total_cans=round(sum([x['n_cans'] for x in results_grouped]), 1),
                               width=width, height=height, m2_per_can=m2_per_can, layers=layers)

    return render_template('tools.html')


@tools.route('/palette', methods=['GET', 'POST'])
def generate_palette():
    if 'generate' in request.form:
        color_list = request.form.get('colors').split(' ')
        aco = generate_aco(color_list)
        return send_file(filename_or_fp=aco, as_attachment=True,
                         mimetype='application/octet-stream', attachment_filename='palette.aco')
    else:
        return render_template('palette.html')


def generate_aco(color_list):
    aco = Aco()

    for color in color_list:
        color_code = color.split('|')[0]
        color_name = color.split('|')[1]

        r = int(color_code[1:3], base=16)
        g = int(color_code[3:5], base=16)
        b = int(color_code[5:7], base=16)

        aco.add(color_name, r, g, b)

    return aco.as_bytea()


def compare_colors(a, b):
    color1_lab = convert_color(sRGBColor(*(a / 256)), LabColor)
    color2_lab = convert_color(sRGBColor(*(b / 256)), LabColor)
    np.asscalar = lambda x: x.item()  # workaround, colormath still uses deprecated and removed function from numpy
    return delta_e_cie2000(color1_lab, color2_lab)


def calculate_colors(image_data):
    image = Image.open(image_data).convert('RGB')

    if image.width > box_dimension or image.height > box_dimension:
        if image.width > image.height:
            result_width = box_dimension
            result_height = round(result_width * (image.height / image.width))
        else:
            result_height = box_dimension
            result_width = round(result_height * (image.width / image.height))

        image = image.resize((result_width, result_height), resample=Image.NEAREST)

    pixels = np.array(image).reshape(image.width * image.height, 3)
    min_pixels_per_color = int(len(pixels) * smallest_area_ratio)

    unique_colors, unique_color_counts = np.unique(pixels, axis=0, return_counts=True)
    unique_significant_color_indexes = np.where(unique_color_counts >= min_pixels_per_color)
    unique_colors = unique_colors[unique_significant_color_indexes]

    model = DBSCAN(eps=color_merge_tolerance, min_samples=1, metric=compare_colors).fit(unique_colors)
    truly_unique_colors = []

    for label in np.unique(model.labels_):
        color = np.apply_along_axis(lambda x: int(round(np.mean(x))), 0,
                                    unique_colors[np.where(model.labels_ == label)])
        truly_unique_colors.append(tuple(color))

    # calculating unique color mask
    unique_color_counts = {}
    pixel_color_mask = []

    for pixel in pixels:
        distances = [np.linalg.norm(pixel - color) for color in truly_unique_colors]
        # distances = [compare_colors(np.array(pixel), np.array(color)) for color in truly_unique_colors]

        best_color_idx = np.argmin(distances)
        best_color = truly_unique_colors[best_color_idx]

        if best_color not in unique_color_counts:
            unique_color_counts[best_color] = 0

        unique_color_counts[best_color] += 1
        pixel_color_mask.append(best_color)

    # replacing with realistic colors
    pixel_color_mask = np.array(pixel_color_mask)
    real_color_counts = {}

    for color in truly_unique_colors:
        color_mask_indexes = np.where(pixel_color_mask == color)[0]
        original_image_pixels = pixels[color_mask_indexes]
        original_color = np.apply_along_axis(lambda x: int(round(np.mean(x))), 0, original_image_pixels)

        text_color = '#000' if max(original_color) > 72 else '#fff'
        bg_color = '#{0:02x}{1:02x}{2:02x}'.format(original_color[0], original_color[1], original_color[2])

        real_color_counts[tuple(original_color)] = (round(unique_color_counts[color] / len(pixels) * 100, 1),
                                                    bg_color, text_color)

    # preparing outputs
    buffered = BytesIO()
    image.save(buffered, format='JPEG')
    base64_img = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return base64_img, sorted(real_color_counts.items(), key=lambda x: x[0], reverse=True)
