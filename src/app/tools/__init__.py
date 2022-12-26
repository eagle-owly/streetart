from flask import Blueprint

tools = Blueprint('tools', __name__, template_folder='templates', static_folder='static')

from app.tools import routes
