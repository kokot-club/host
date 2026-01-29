from flask import Blueprint, request, make_response, redirect, jsonify
from web.utils.generators import random_string
from web.utils.networking import verify_cloudflare_challenge
from web.middleware.auth import set_user_cookie, clear_user_cookie, require_access, get_current_user
from web.models.user import User
from web.models.role import UserRole
from web.models.invites import Invite
from web.models.db import DB

bp_backend = Blueprint('backend', __name__, url_prefix='/api')

@bp_backend.route('/user/login', methods=['POST'])
def user_login():
    if request.form:
        username = request.form.get('user', None)
        password = request.form.get('password', None)
        challenge = request.form.get('challenge', None)

        if not verify_cloudflare_challenge(challenge):
            return jsonify({
                'error': 'Captcha is required'
            }), 400

        if not username or not password:
            # missing form data

            return jsonify({
                'error': 'No username or password provided'
            }), 400

        user = User.from_username(username)
        if not user:
            # user doesnt exist

            return jsonify({
                'error': 'User doesn\'t exist'
            }), 400


        if not user.password_matches_hash(password):
            # password doesnt match

            return jsonify({
                'error': 'Password doesn\'t match username'
            }), 400
    
        # success!
        response = make_response(jsonify({
            'did_login': True
        }))
        response = set_user_cookie({
            'uid': user.uid,
            'username': user.username,
        }, response)

        return response

    # invalid request
    return jsonify({
        'error': 'Bad request'
    }), 400

@bp_backend.route('/user/register', methods=['POST'])
def user_register():
    if request.form:
        username = request.form.get('user', None)
        password = request.form.get('password', None)
        invite = request.form.get('invite', None)
        challenge = request.form.get('challenge', None)

        if not verify_cloudflare_challenge(challenge):
            return jsonify({
                'error': 'Captcha is required'
            }), 400

        if not username or not password or not invite:
            # missing form data

            return jsonify({
                'error': 'No username, password or invite provided'
            }), 400
        
        if not username.isalnum():
            # username contains special characters

            return jsonify({
                'error': 'Illegal characters in username'
            }), 400
        
        if len(username) > 20:
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

        user_invite = Invite.from_hash(invite)
        if not user_invite:
            # invite doesnt exist or it was already used

            return jsonify({
                'error': 'Invite doesn\'t exist or it was already used'
            }), 400
        
        if User.from_username(username):
            # user already exists

            return jsonify({
                'error': 'Username is already taken'
            }), 400


        # success! lets create an user
        new_user = User.create(username=username, password=password, role=UserRole.USER.value)
        user_invite.set_claimed(new_user.uid)
        
        return jsonify({
            'msg': 'Account created! You can now log in'
        }), 200
    
    # invalid request
    return jsonify({
        'error': 'Bad request'
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
        'role': user.role,
    }), 200

@bp_backend.route('/user/settings', methods=['GET', 'POST'])
@require_access(level=UserRole.USER)
def user_settings():
    user = get_current_user()

    with DB.get().cursor() as cursor:
        match request.method:
            case 'GET':
                return jsonify(user.get_settings()), 200
            case 'POST':
                if request.form:
                    user.set_settings(request.form)

                return jsonify({
                    'msg': 'OK'
                }), 200

    return jsonify({
        'error': 'Bad request'
    }), 400

@bp_backend.route('/admin/generate_invite', methods=['POST'])
@require_access(level=UserRole.ADMIN)
def admin_generate_invite():
    invite = Invite.create(random_string(32))
    if invite:
        return jsonify({
            'invite': invite.hash_
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

    for user in User.get_all():
        result['users'].append({
            'id': user.uid,
            'username': user.username,
            'join_date': 'idk',
            'role': user.role
        })
    
    return jsonify(result), 200
