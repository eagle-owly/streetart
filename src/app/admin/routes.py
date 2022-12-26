from functools import wraps
from datetime import datetime

from flask import render_template, session, redirect, request
from . import admin
from app.__main__ import db, app


def login_required(func):
    @wraps(func)
    def secure_function(*args, **kwargs):
        if 'vault_approved' not in session:
            return redirect('/vault')

        return func(*args, **kwargs)

    return secure_function


@admin.route('/', methods=['GET', 'POST'])
def vault():
    if request.form:
        signed_in = request.form.get('password') == app.config['ADMIN_PASSWORD']

        if signed_in:
            session['vault_approved'] = True

    if 'vault_approved' in session:
        return redirect('/vault/logs/0')
    else:
        return render_template('login.html')


@admin.route('/leave_vault')
@login_required
def logout():
    session.clear()
    return redirect('/vault')


@admin.route('/logs/<page>')
@login_required
def logs(page):
    page = int(page)
    raw_activity_logs = db.get_activity_logs(page)

    sessions = {}

    for a in raw_activity_logs:
        if a['id'] not in sessions:
            sessions[a['id']] = {'ip_address': a['ip_address'], 'user_agent': a['user_agent'],
                                 'test_name': a['test_name'], 'content': a['content'], 'place': a['place'],
                                 'events': [], 'total_seconds': 0, 'created': a['created']}

        sessions[a['id']]['events'].append({'event': a['event'], 'details': a['details'],
                                            'seconds': a['seconds'], 'created': a['created']})
        sessions[a['id']]['total_seconds'] += a['seconds']

    return render_template('logs.html', sessions=sessions, page=page)


@admin.route('/delete/<page>/<session_id>')
@login_required
def delete(page, session_id):
    page = int(page)
    session_id = int(session_id)

    db.delete_session(session_id)
    return redirect(f'/vault/logs/{page}')


@admin.route('/places')
@login_required
def places():
    return render_template('places.html')


@admin.route('/stats')
@login_required
def stats():
    raw_stats = db.get_stats()
    grouped_stats = {}

    for s in raw_stats:
        if s['place'] not in grouped_stats:
            grouped_stats[s['place']] = {}
        if s['choice'] not in grouped_stats[s['place']]:
            grouped_stats[s['place']][s['choice']] = {}
        if s['content'] not in grouped_stats[s['place']][s['choice']]:
            grouped_stats[s['place']][s['choice']][s['content']] = {}

        for k, v in s.items():
            if k in ['place', 'choice', 'content']:
                continue

            grouped_stats[s['place']][s['choice']][s['content']][k] = v

            if k == 'deactivated':
                grouped_stats[s['place']][s['choice']][s['content']]['time_until'] = v if v is not None else datetime.now()

    return render_template('stats.html', grouped_stats=grouped_stats)
