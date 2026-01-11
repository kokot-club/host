import os
import subprocess
from flask import Blueprint, Response, send_file, request, jsonify, redirect
from mimetypes import guess_type
from datetime import datetime, timedelta
from shared.db import DB
from shared.auth import require_access, get_current_user, get_real_host, get_user_upload_key, set_user_upload_key, get_user_settings
from shared.generators import random_string, qr_code, sxcu_file, file_page
from shared.utils import is_exiftool_installed
from shared.models import UserRole

bp_files = Blueprint('files', __name__)

MAX_UPLOAD_SIZE_MB = float(os.environ.get('MAX_UPLOAD_SIZE_MB', 80.0))
STORAGE_PER_USER_MB = float(os.environ.get('STORAGE_PER_USER_MB', 250.0))
ALLOWED_MIMETYPES = os.environ.get('ALLOWED_MIMETYPES', '')
ALLOWED_MIMETYPES_INVERSE = int(os.environ.get('ALLOWED_MIMETYPES_INVERSE', 0)) == 1

upload_folder = os.path.join(os.getcwd(), 'uploads')
os.makedirs(upload_folder, exist_ok=True)

def generate_upload_key():
    return random_string(120)

def get_user_upload_data(user_id=-1):
    with DB.get().cursor() as cursor:
        cursor.execute(
            'SELECT COUNT(f.id), SUM(f.size_mb), u.fixed_storage_mb FROM files AS f JOIN users AS u ON u.id = f.owner_id WHERE f.owner_id = ?',
            (user_id,)
        )
        result = cursor.fetchone()
        if result:
            return result[0], round(result[1] or 0, 2), result[2] or STORAGE_PER_USER_MB
        
def get_file_record(target):
    target_key = target.replace('.gif', '')
    with DB.get().cursor() as cursor:
        cursor.execute('SELECT path, filename, expires, mimetype, owner_id, size_mb, uploaded_at FROM files WHERE uri = ?', (target_key,))
        record = cursor.fetchone()
        if not record:
            return None

        if record[2] and datetime.strptime(record[2], '%Y-%m-%d %H:%M:%S') < datetime.now():
            file_delete(uri=target, force=True)

            return None

        return record

@bp_files.route('/files/upload', methods=['POST'])
@require_access(level=UserRole.USER, api_keys=True)
def file_upload():
    uploaded_file = request.files.get('file')
    if not uploaded_file or uploaded_file.filename == '':
        return jsonify({
            'error': 'No file uploaded'
        }), 400
    
    owner_id = get_current_user().uid
    user_total_uploads, user_usage, user_storage = get_user_upload_data(owner_id)
    user_settings = get_user_settings(owner_id)
    if user_total_uploads is None or user_usage is None or user_storage is None or user_settings is None:
        return jsonify({
            'error': 'Internal server error'
        }), 500
    
    size_mb = round(max(uploaded_file.content_length or len(uploaded_file.stream.read()), 10486) / 1024**2, 2)
    uploaded_file.stream.seek(0)

    if user_usage + size_mb > user_storage:
        return jsonify({
            'error': 'This upload will exceed max. storage capacity'
        }), 413
    
    if size_mb > MAX_UPLOAD_SIZE_MB:
        return jsonify({
            'error': 'File is too large'
        }), 413
    
    filename = uploaded_file.filename
    if len(filename) > 100:
        return jsonify({
            'error': 'File name is too long'
        }), 400

    mime_type = guess_type(filename)[0] or filename.split('.')[-1]
    if not mime_type:
        return jsonify({
            'error': f'Unknown mime type'
        }), 400

    allow_upload = False
    for allowed_mime in ALLOWED_MIMETYPES.split(';'):
        if allowed_mime and allowed_mime in mime_type:
            allow_upload = not ALLOWED_MIMETYPES_INVERSE
            break

    if not allow_upload:
        return jsonify({
            'error': f'Illegal mime type: {mime_type}'
        }), 400

    location = random_string(7)
    file_path = os.path.join(upload_folder, location)
    uploaded_file.save(file_path)

    if is_exiftool_installed():
        try:
            subprocess.run(['exiftool', '-all=', '-overwrite_original', file_path])
        except BaseException:
            print('Error running exiftool, metadata is still present')

    expires_at = None
    file_ttl = user_settings.get('auto_expire', 0)
    if file_ttl > 0:
        expires_at = (datetime.now() + timedelta(seconds=file_ttl)).strftime('%Y-%m-%d %H:%M:%S')

    with DB.get().cursor() as cursor:
        cursor.execute(
            'INSERT INTO files (owner_id, filename, path, uri, size_mb, mimetype, expires) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (owner_id, filename, file_path, location, size_mb, mime_type, expires_at)
        )

    file_url = f'{get_real_host()}uploads/{location}{mime_type.endswith('gif') and '.gif' or ''}'
    return jsonify({
        'url': file_url,
        'deletion_url': f'{get_real_host()}files/delete?uri={location}',
        'qr_code': 'data:image/png;base64,' + qr_code(file_url)
    }), 200

@bp_files.route('/files/delete', methods=['DELETE'])
@require_access(level=UserRole.USER, api_keys=True)
def file_delete(uri=None, force=False):
    uri = uri or request.args.get('uri', type=str)
    user_level = get_current_user().role
    owner_id = get_current_user().uid

    with DB.get().cursor() as cursor:
        cursor.execute(
            'SELECT path, owner_id, expires FROM files WHERE uri = ?',
            (uri,)
        )
        result = cursor.fetchone()
        if result and (force or result[1] == owner_id or user_level == UserRole.ADMIN):
            os.remove(result[0])
            cursor.execute(
                'DELETE FROM files WHERE uri = ?',
                (uri,)
            )

            return jsonify({}), 200
        
    return jsonify({
        'error': 'Bad request'
    }), 401

@bp_files.route('/files/edit', methods=['PATCH'])
@require_access(level=UserRole.USER, api_keys=True)
def file_edit():
    target_uri = request.json.get('uri')
    if not target_uri or target_uri == '':
        return jsonify({
            'error': 'Bad request'
        }), 401
    
    record = get_file_record(target_uri)
    if not record:
        return jsonify({
            'error': 'File not found or expired'
        }), 404

    new_filename = request.json.get('new_filename')
    if new_filename:
        if len(new_filename) > 100:
            return jsonify({
                'error': 'New file name is too long'
            }), 400

        with DB.get().cursor() as cursor:
            cursor.execute(
                'UPDATE files SET filename=? WHERE uri=?',
                (new_filename, target_uri,)
            )

    return jsonify({
        'msg': 'OK'
    }), 200

@bp_files.route('/files/summary')
@require_access(level=UserRole.USER)
def file_summary():
    owner_id = get_current_user().uid
    total_uploads, total_usage, user_storage = get_user_upload_data(owner_id)

    return jsonify({
        'uploads': total_uploads,
        'usage_mb': total_usage,
        'storage_mb': user_storage
    }), 200

@bp_files.route('/files/get')
@require_access(level=UserRole.USER)
def file_get():
    result = []
    owner_id = get_current_user().uid

    pos = request.args.get('pos', default=1, type=int)
    query = request.args.get('query', default='*', type=str).replace('*', '%')
    max_ = request.args.get('max', default=50, type=int)

    with DB.get().cursor() as cursor:
        cursor.execute(
            'SELECT uri FROM files WHERE owner_id = ? AND filename LIKE ? ORDER BY uploaded_at DESC LIMIT ? OFFSET ?',
            (owner_id, query, max_, pos)
        )
        for (uri,) in cursor.fetchall():
            record = get_file_record(uri)
            if not record:
                continue

            path, filename, expires, mimetype, owner_id, size_mb, uploaded_at, *_ = record
            result.append({
                'filename': filename,
                'thumbnail': 'image' in mimetype and f'{get_real_host()}files/uploads/{uri}' or '/static/images/no-preview.png',
                'uri': uri,
                'url': f'{get_real_host()}uploads/{uri}{mimetype.endswith("gif") and ".gif" or ""}',
                'size_mb': size_mb,
                'uploaded_at': uploaded_at,
                'expires_at': expires
            })

    return jsonify(result), 200

@bp_files.route('/files/regenerate_upload_key', methods=['POST'])
@require_access(level=UserRole.USER)
def regenerate_upload_key():
    upload_key = generate_upload_key()
    set_user_upload_key(upload_key)
    
    return jsonify({
        'msg': 'Success resetting key' 
    }), 200

@bp_files.route('/files/integration')
@require_access(level=UserRole.USER)
def request_integration():
    upload_key = get_user_upload_key()
    if not upload_key:
        did_generate_key = regenerate_upload_key()

        return request_integration()

    integration_type = request.args.get('integration_type', type=str)
    if upload_key and integration_type:
        match integration_type:
            case 'sharex':
                return Response(
                    sxcu_file(get_real_host(), upload_key),
                    mimetype='text/plain',
                    headers={
                        'Content-Disposition': f'attachment; filename=sharex_{random_string(6)}.sxcu'
                    },
                    status=200
                )

    return jsonify({
        'error': 'Bad request' 
    }), 401

@bp_files.route('/files/uploads/<target>')
def serve_file(target):
    record = get_file_record(target)
    if not record:
        return jsonify({
            'error': 'File not found or expired'
        }), 404

    file_path, filename, expires, *_ = record
    if not file_path:
        return jsonify({
            'error': 'File is missing on the server'
        }), 404

    return send_file(file_path, download_name=filename, as_attachment=True)

@bp_files.route('/uploads/<target>')
def serve_rich_file(target):
    raw_file = f'{get_real_host()}files/uploads/{target}'
    record = get_file_record(target)
    if not record:
        return jsonify({
            'error': 'File not found or expired'
        }), 404

    _, filename, _, mimetype, owner_id, size_mb, uploaded_at, *_ = record

    is_discord = 'discordbot' in request.headers.get('User-Agent', '').lower()
    if is_discord and mimetype.startswith('video'):
        return redirect(raw_file)

    return file_page(
        file_url=raw_file,
        file_type=mimetype,
        filename=filename,
        file_size_mb=size_mb,
        file_date=uploaded_at,
        uploader_id=owner_id
    )