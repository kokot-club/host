import os
import subprocess
from flask import Blueprint, Response, request, jsonify
from mimetypes import guess_type
from datetime import datetime, timedelta
from web.utils.system import is_exiftool_installed
from web.utils.generators import api_key, random_string, sxcu_config
from web.middleware.auth import require_access, get_current_user
from web.models.role import UserRole
from web.models.files import File

bp_files = Blueprint('files', __name__)

MAX_UPLOAD_SIZE_MB = float(os.environ.get('MAX_UPLOAD_SIZE_MB', 80.0))
ALLOWED_MIMETYPES = os.environ.get('ALLOWED_MIMETYPES', '')
ALLOWED_MIMETYPES_INVERSE = int(os.environ.get('ALLOWED_MIMETYPES_INVERSE', 0)) == 1

upload_folder = os.path.join(os.getcwd(), 'uploads')
os.makedirs(upload_folder, exist_ok=True)

@bp_files.route('/files/upload', methods=['POST'])
@require_access(level=UserRole.USER, api_keys=True)
def file_upload():
    uploaded_file = request.files.get('file')
    if not uploaded_file or uploaded_file.filename == '':
        return jsonify({
            'error': 'No file uploaded'
        }), 400
    
    user = get_current_user()
    user_settings = user.get_settings()
    user_usage = user.get_storage_usage_mb()
    user_storage = user.get_storage_space_mb()

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

    mimetype = guess_type(filename)[0] or filename.split('.')[-1]
    if not mimetype:
        return jsonify({
            'error': f'Unknown mime type'
        }), 400

    allow_upload = False
    for allowed_mime in ALLOWED_MIMETYPES.split(';'):
        if allowed_mime and allowed_mime in mimetype:
            allow_upload = not ALLOWED_MIMETYPES_INVERSE
            break

    if not allow_upload:
        return jsonify({
            'error': f'Illegal mime type: {mimetype}'
        }), 400

    file_uri = random_string(7)
    file_path = os.path.join(upload_folder, file_uri)

    expires_at = None
    file_ttl = user_settings.get('auto_expire', 0)
    if file_ttl > 0:
        expires_at = (datetime.now() + timedelta(seconds=file_ttl)).strftime('%Y-%m-%d %H:%M:%S')

    file = File.upload(uploader=user, filename=filename, uri=file_uri, path=file_path, size_mb=size_mb, mimetype=mimetype, expires=expires_at)
    if file:
        uploaded_file.save(file_path)

        if is_exiftool_installed():
            try:
                subprocess.run(['exiftool', '-all=', '-overwrite_original', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except BaseException:
                print('Error running exiftool, metadata is still present')

        return jsonify({
            'url': file.get_url(),
            'deletion_url': file.get_deletion_url()
        }), 200

@bp_files.route('/files/delete', methods=['DELETE'])
@require_access(level=UserRole.USER, api_keys=True)
def file_delete():
    uri = request.args.get('uri', type=str)
    if not uri:
        return jsonify({
            'error': 'No URI provided'
        }), 401

    user = get_current_user()
    user_level = user.role
    user_id = user.uid

    file = File.from_uri(uri)
    if file:
        if file.owner_id != user_id or user_level < UserRole.ADMIN.value:
            return jsonify({
                'error': 'You are not allowed to delete this file'
            }), 403
        
        file.delete()
        return jsonify({
            'msg': 'OK'
        }), 200
    else:
        return jsonify({
            'error': 'File not found or expired'
        }), 404

@bp_files.route('/files/edit', methods=['PUT'])
@require_access(level=UserRole.USER, api_keys=True)
def file_edit():
    uri = request.json.get('uri')
    if not uri:
        return jsonify({
            'error': 'No URI provided'
        }), 401

    user = get_current_user()
    user_level = user.role
    user_id = user.uid

    file = File.from_uri(uri)
    if file:
        if file.owner_id != user_id or user_level < UserRole.ADMIN.value:
            return jsonify({
                'error': 'You are not allowed to edit this file'
            }), 403
        
        new_filename = request.json.get('new_filename')
        if new_filename:
            if len(new_filename) > 100:
                return jsonify({
                    'error': 'New file name is too long'
                }), 400

            file.modify(new_filename=new_filename)

        return jsonify({
            'msg': 'OK'
        }), 200
    else:
        return jsonify({
            'error': 'File not found or expired'
        }), 404

@bp_files.route('/files/summary')
@require_access(level=UserRole.USER)
def file_summary():
    user = get_current_user()

    return jsonify({
        'uploads': len(user.get_uploaded_files()),
        'usage_mb': user.get_storage_usage_mb(),
        'storage_mb': user.get_storage_space_mb()
    }), 200

@bp_files.route('/files/get')
@require_access(level=UserRole.USER)
def file_get():
    result = []
    
    user = get_current_user()

    offset = request.args.get('pos', default=1, type=int)
    query = request.args.get('query', default='*', type=str).replace('*', '%')
    max_files = request.args.get('max', default=50, type=int)

    for uploaded_file in user.get_uploaded_files(query=query, max_files=max_files, offset=offset):
        result.append({
            'filename': uploaded_file.filename,
            'thumbnail': uploaded_file.get_thumbnail(),
            'uri': uploaded_file.uri,
            'url': uploaded_file.get_url(),
            'size_mb': uploaded_file.size_mb,
            'uploaded_at': uploaded_file.uploaded_at,
            'expires_at': uploaded_file.expires
        })

    return jsonify(result), 200

@bp_files.route('/files/regenerate_upload_key', methods=['POST'])
@require_access(level=UserRole.USER)
def regenerate_upload_key():
    user = get_current_user()

    new_key = api_key()
    user.set_api_key(new_key)

    return jsonify({
        'msg': 'Success resetting key' 
    }), 200

@bp_files.route('/files/integration')
@require_access(level=UserRole.USER)
def request_integration():
    user = get_current_user()
    user_upload_key = user.get_api_key()
    if not user_upload_key:
        did_generate_key = regenerate_upload_key()

        return request_integration()

    integration_type = request.args.get('integration_type', type=str)
    if user_upload_key and integration_type:
        match integration_type:
            case 'sharex':
                return Response(
                    sxcu_config(user_upload_key),
                    mimetype='text/plain',
                    headers={
                        'Content-Disposition': f'attachment; filename=sharex_{random_string(6)}.sxcu'
                    },
                    status=200
                )

    return jsonify({
        'error': 'Bad request' 
    }), 401
