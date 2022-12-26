from flask import Blueprint

streetart = Blueprint('streetart', __name__, template_folder='templates',
                      static_folder='static', static_url_path='/s')

from app.streetart import routes
