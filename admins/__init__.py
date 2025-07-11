from  flask import Blueprint
admins_bp = Blueprint(
    'admins', __name__,
    template_folder='templates',
    url_prefix="/admins",
    static_folder='static'
)
from . import routes