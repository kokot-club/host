import os
from datetime import timedelta
from pathlib import Path
from flask import Blueprint, send_from_directory, render_template, abort, redirect, jsonify, send_file, request
from web.middleware.ratelimit import is_ip_ratelimited
from web.middleware.auth import get_current_user
from web.models.user import User
from web.models.role import UserRole
from web.models.files import File

bp_frontend = Blueprint('web', __name__, static_folder=None,
    template_folder=os.path.join(os.getcwd(), 'src', 'web', 'templates'))

CLOUDFLARE_TURNSTILE_SITE = os.environ.get('CLOUDFLARE_TURNSTILE_SITE')
SUPPORT_HANDLE = os.environ.get('SUPPORT_HANDLE')
DISCORD_APP_CLIENT_SECRET = os.environ.get('DISCORD_APP_CLIENT_SECRET')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

@bp_frontend.context_processor
def inject_globals():
    return {
        'current_user': get_current_user(),
        'turnstile_site_key': CLOUDFLARE_TURNSTILE_SITE,
        'support_handle': SUPPORT_HANDLE,
        'discord_linking_enabled': (DISCORD_BOT_TOKEN and DISCORD_APP_CLIENT_SECRET) != None
    }

@bp_frontend.route('/static/<path:target>')
def serve_static(target):
    user = get_current_user()
    user_role = user != None and user.role or UserRole.ADMIN.value

    match Path(target).parent.name.lower():
        case 'user':
            if user_role < UserRole.USER.value:
                return abort(403)
        case 'admin':
            if user_role < UserRole.ADMIN.value:
                return abort(403)
    
    return send_from_directory(os.path.join(os.getcwd(), 'src', 'static'), target)

@bp_frontend.route('/')
def serve_app():
    return render_template('app.html')

@bp_frontend.route('/files/uploads/<uri>')
def files_serve_file(uri):
    file = File.from_uri(uri)
    if not file:
        return jsonify({
            'error': 'File not found or expired'
        }), 404

    file_path = file.path
    if not file_path:
        return jsonify({
            'error': 'Internal server error'
        }), 500

    return send_file(file_path, download_name=file.filename, as_attachment=True)

@bp_frontend.route('/uploads/<uri>')
def files_serve_rich_file(uri):
    file = File.from_uri(uri)
    if not file:
        return jsonify({
            'error': 'File not found or expired'
        }), 404

    is_discord = 'discordbot' in request.headers.get('User-Agent', '').lower()
    if is_discord and file.mimetype.startswith('video'):
        return files_serve_file(file.uri)
    
    if not is_ip_ratelimited(timedelta(days=999)):
        file.increment_views()

    uploader = User.from_uid(file.owner_id)
    uploader_settings = uploader.get_settings()

    dynamic_strings = {}
    placeholders = {
        r'%date%': file.uploaded_at,
        r'%size%': file.size_mb,
        r'%owner%': uploader.get_display_name(),
        r'%filename%': file.filename
    }

    for key in ['embed_sitename', 'embed_authorname', 'embed_description', 'embed_title']:
        text = uploader_settings.get(key)
        if text:
            for placeholder, val in placeholders.items():
                text = text.replace(placeholder, str(val))

            dynamic_strings[key] = text

    return render_template('file.html', file=file, uploader=uploader, **dynamic_strings)

@bp_frontend.app_errorhandler(404)
@bp_frontend.app_errorhandler(500)
def catch_all(_):
    return redirect('/#!/error')
