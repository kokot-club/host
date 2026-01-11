import os
from pathlib import Path
from flask import Blueprint, send_from_directory, abort, redirect
from shared.auth import get_current_user
from shared.models import UserRole

bp_frontend = Blueprint('web', __name__, static_folder=None)

STATIC_FOLDER = os.path.join(os.getcwd(), 'src', 'web', 'static')

@bp_frontend.route('/static/<path:target>')
def serve_static(target):
    user = get_current_user()
    user_role = user != None and user.role or UserRole.ADMIN

    match Path(target).parent.name.lower():
        case 'user':
            if user_role.value < UserRole.USER.value:
                return abort(403)
        case 'admin':
            if user_role.value < UserRole.ADMIN.value:
                return abort(403)
    
    return send_from_directory(STATIC_FOLDER, target)

@bp_frontend.route('/')
def serve():
    return send_from_directory(STATIC_FOLDER, 'index.html')

@bp_frontend.app_errorhandler(404)
def catch_all(error):
    return redirect('/#!/error')

@bp_frontend.app_errorhandler(500)
def catch_all(error):
    return redirect('/#!/error')