from flask import Blueprint, request, make_response, redirect, jsonify
from dataclasses import asdict
from werkzeug.security import generate_password_hash, check_password_hash
from shared.models import User, UserRole
from shared.auth import set_user_cookie, clear_user_cookie, require_access, get_current_user, get_user_settings, verify_cloudflare_challenge
from shared.generators import random_string
from shared.db import DB

bp_backend = Blueprint('backend', __name__, url_prefix='/api')

def is_hex(hex_str):
    if hex_str.startswith('#') and len(hex_str) == 7:
        return hex_str
    
    return '#000000'

def is_url(url_str):
    if url_str.startswith(('http://', 'https://')):
        return url_str
    
    return ''

@bp_backend.route('/user/login', methods=['POST'])
def user_login():
    if request.form:
        user = request.form.get('user', None)
        password = request.form.get('password', None)
        challenge = request.form.get('challenge', None)

        if not verify_cloudflare_challenge(challenge):
            return jsonify({
                'error': 'Captcha is required'
            }), 400

        if not user or not password:
            # missing form data

            return jsonify({
                'error': 'No username or password provided'
            }), 400

        with DB.get().cursor() as cursor:
            cursor.execute('SELECT password, id, username, role FROM users WHERE LOWER(username) = LOWER(?)', (user,))
            result = cursor.fetchone()
            if not result:
                # user doesnt exist

                return jsonify({
                    'error': 'User doesn\'t exist'
                }), 400

            if not check_password_hash(result[0], password):
                # password doesnt match

                return jsonify({
                    'error': 'Password doesn\'t match username'
                }), 400
        
            # success!
            user_data = User(uid=result[1], username=result[2], role=result[3])

            response = make_response(jsonify({
                'did_login': True
            }))
            response = set_user_cookie(asdict(user_data), response)

            return response

    # invalid request
    return jsonify({
        'error': 'Bad request'
    }), 400

@bp_backend.route('/user/register', methods=['POST'])
def user_register():
    if request.form:
        user = request.form.get('user', None)
        password = request.form.get('password', None)
        invite = request.form.get('invite', None)
        challenge = request.form.get('challenge', None)

        if not verify_cloudflare_challenge(challenge):
            return jsonify({
                'error': 'Captcha is required'
            }), 400

        if not user or not password or not invite:
            # missing form data

            return jsonify({
                'error': 'No username, password or invite provided'
            }), 400
        
        if not user.isalnum():
            # username contains special characters

            return jsonify({
                'error': 'Illegal characters in username'
            }), 400
        
        if len(user) > 20:
            # username is too long

            return jsonify({
                'error': 'Username is too long'
            }), 400

        if len(password) < 8:
            # password is too short

            return jsonify({
                'error': 'Password is too short'
            }), 400
        
        if len(password) > 200:
            # password is too long

            return jsonify({
                'error': 'Password is too long'
            }), 400

        with DB.get().cursor() as cursor:
            cursor.execute('SELECT 1 FROM invites WHERE hash = ? AND user_id IS NULL', (invite,))
            if not cursor.fetchone():
                # invite doesnt exist or it was already used

                return jsonify({
                    'error': 'Invite doesn\'t exist or it was already used'
                }), 400

            cursor.execute('SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)', (user,))
            if cursor.fetchone():
                # user already exists

                return jsonify({
                    'error': 'Username is already taken'
                }), 400
            
            # success! lets create an user
            password_hash = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, 0)',
                (user, password_hash,)
            ),

            new_user_id = cursor.lastrowid
            if new_user_id == 1:
                cursor.execute('UPDATE users SET role = 2 WHERE id = 1')
            cursor.execute(
                'UPDATE invites SET user_id = ? WHERE hash = ?',
                (new_user_id, invite,)
            )
            cursor.execute(
                'INSERT INTO settings (user_id) VALUES (?)',
                (new_user_id,)
            ),
            
            return jsonify({
                'msg': 'Account created! You can now log in'
            }), 200
    
    # invalid request
    return jsonify({
        'error': 'Password doesn\'t match username'
    }), 400

@bp_backend.route('/user/logout')
def user_logout():
    return clear_user_cookie(make_response(redirect('/')))

@bp_backend.route('/user/me')
@require_access(level=UserRole.USER)
def user_me():
    user = get_current_user()

    return jsonify({
        'username': user.username,
        'uid': user.uid,
        'role': user.role.value,
    }), 200

@bp_backend.route('/user/settings', methods=['GET', 'POST'])
@require_access(level=UserRole.USER)
def user_settings():
    user = get_current_user()

    with DB.get().cursor() as cursor:
        match request.method:
            case 'GET':
                return jsonify(get_user_settings(user.uid)), 200
            case 'POST':
                data = request.form
                cursor.execute(
                    """
                    UPDATE settings
                    SET
                        embed_color = ?,
                        embed_title = ?,
                        embed_sitename = ?,
                        embed_siteurl = ?,
                        embed_authorname = ?,
                        embed_authorurl = ?,
                        embed_description = ?,
                        anonymous = ?,
                        auto_expire = ?
                    WHERE user_id = ?
                    """,
                    (
                        is_hex(data.get('embed_color', '')),
                        data.get('embed_title', '')[:40],
                        data.get('embed_sitename', '')[:40],
                        is_url(data.get('embed_siteurl', ''))[:100],
                        data.get('embed_authorname', '')[:200],
                        is_url(data.get('embed_authorurl', ''))[:100],
                        data.get('embed_description', '')[:200],
                        str(data.get('anonymous', '')).lower() == 'true',
                        min(max(int(data.get('auto_expire', '0')), 0), 604800),
                        user.uid
                    )
                )

                if cursor.rowcount:
                    return jsonify({
                        'msg': 'OK'
                    }), 200
                
                return jsonify({
                    'error': 'Internal error'
                }), 500

    return jsonify({
        'error': 'Bad request'
    }), 400

@bp_backend.route('/admin/generate_invite', methods=['POST'])
@require_access(level=UserRole.ADMIN)
def admin_generate_invite():
    invite = random_string(32)

    with DB.get().cursor() as cursor:
        cursor.execute('INSERT INTO invites VALUES (?, NULL)', (invite,))
    
    return jsonify({
        'invite': invite
    }), 200

@bp_backend.route('/admin/purge_invites', methods=['POST'])
@require_access(level=UserRole.ADMIN)
def admin_purge_invites():
    with DB.get().cursor() as cursor:
        cursor.execute('DELETE FROM invites WHERE user_id IS NULL')
    
        return jsonify({
            'msg': f'Deleted {cursor.rowcount} invite(s)'
        }), 200

@bp_backend.route('/admin/list_users', methods=['GET'])
@require_access(level=UserRole.ADMIN)
def admin_list_users():
    result = {
        'users': []
    }

    with DB.get().cursor() as cursor:
        cursor.execute('SELECT id, username, join_date, role FROM users')
        for row in cursor.fetchall():
            result['users'].append({
                'id': row[0],
                'username': row[1],
                'join_date': row[2],
                'role': row[3]
            })
    
    return jsonify(result), 200
