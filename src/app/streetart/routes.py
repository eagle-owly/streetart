import random
import datetime

from flask import render_template, request, session
from . import streetart
from .event import Event
from app.__main__ import db, app


def get_ip_address(request):
    behind_proxy_ip = request.headers.get('X-Real-Ip')
    return behind_proxy_ip if behind_proxy_ip is not None else request.remote_addr


def get_template_by_probability(place_id):
    content_options = db.get_content_options(place_id)
    content_prob = random.uniform(0, 1)

    for option in content_options:
        content_prob -= option['probability']

        if content_prob <= 0:
            return option['id'], option['template']


def get_from_session(place_id):
    if 'id' not in session:
        session_id = int(round(datetime.datetime.now().timestamp(), 2) * 100 - 1e11)
        content_id, chosen_template = get_template_by_probability(place_id)

        session['id'] = session_id
        session['content_id'] = content_id
        session['chosen_template'] = chosen_template

    return session['id'], session['content_id'], session['chosen_template']


@streetart.route('/go/<place_id>')
@streetart.route('/<place_id>')
def place(place_id):
    place_id = place_id[:4]

    if not db.is_place_existing(place_id):
        return render_template('error.html'), 404

    ip_address = get_ip_address(request)[:45]
    user_agent = request.headers.get('User-Agent')[:300]
    session_id, content_id, chosen_template = get_from_session(place_id)

    db.log_event(session_id, place_id, content_id, ip_address, user_agent, Event.PAGE_OPEN.name)
    return render_template(chosen_template, place_id=place_id, ig_profile=app.config['IG_PROFILE'])


@streetart.route('/ping', methods=['POST'])
def ping():
    if 'id' not in session:
        return '', 404

    db.update_seconds(session['id'])
    return '', 200


@streetart.route('/log', methods=['POST'])
def log():
    if 'id' not in session:
        return '', 404

    place_id = request.form.get('place_id')[:4]
    event = request.form.get('event')[:25]
    details = request.form.get('details')[:100] if 'details' in request.form else None

    ip_address = get_ip_address(request)[:45]
    user_agent = request.headers.get('User-Agent')[:300]

    db.log_event(session['id'], place_id, session['content_id'], ip_address, user_agent, event, details)
    return '', 200
