import os
import sys
import logging
import datetime
from flask import Flask, session, render_template
from .common.db import Database

app = Flask(__name__)
app.config.from_pyfile('../app.conf', silent=False)

log_filename = os.path.join(app.config['LOG_FILE'])
logging.basicConfig(filename=log_filename, filemode='w', level=logging.INFO, format='%(asctime)s - %(message)s')
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

db = Database(app)

from .admin import admin
from .streetart import streetart
from .tools import tools

app.register_blueprint(streetart, url_prefix='/')
app.register_blueprint(admin, url_prefix='/vault')
app.register_blueprint(tools, url_prefix='/tools')


@app.before_request
def before_request():
    session.permanent = True


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(500)
def error(e):
    return render_template('error.html'), 500


if __name__ == '__main__':
    app.run(ssl_context='adhoc')
    # app.run()
