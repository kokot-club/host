import os
import requests
from datetime import timedelta
from flask import Blueprint, request, make_response, redirect, jsonify
from web.utils.generators import invite_key
from web.utils.networking import verify_cloudflare_challenge, get_real_host, get_real_ip
from web.middleware.ratelimit import ratelimit, is_ip_ratelimited
from web.middleware.auth import set_user_cookie, clear_user_cookie, require_access, get_current_user
from web.models.user import User
from web.models.role import UserRole
from web.models.invites import Invite
from web.models.discord import Discord

bp_backend = Blueprint('backend', __name__, url_prefix='/api')

DISCORD_APP_CLIENT_ID = os.environ.get('DISCORD_APP_CLIENT_ID')
DISCORD_APP_CLIENT_SECRET = os.environ.get('DISCORD_APP_CLIENT_SECRET')
DISCORD_SERVER_ID = os.environ.get('DISCORD_SERVER_ID')

@bp_backend.route('/user/login', methods=['POST'])
def user_login():
    if request.form:
        username = request.form.get('user')
        password = request.form.get('password')
        challenge = request.form.get('challenge')

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
            }), 404

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

@bp_backend.route('/user/trigger_recovery', methods=['POST'])
@ratelimit(timedelta(minutes=1))
def user_trigger_recovery():
    if request.form:
        username = request.form.get('user')
        challenge = request.form.get('challenge')

        if not verify_cloudflare_challenge(challenge):
            return jsonify({
                'error': 'Captcha is required'
            }), 400
        
        if not username:
            # missing form data

            return jsonify({
                'error': 'No username provided'
            }), 400
        
        user = User.from_username(username)
        if not user:
            # user doesnt exist

            return jsonify({
                'error': 'User doesn\'t exist'
            }), 404
        
        linked_discord = user.get_discord_link()
        if not linked_discord or not all(linked_discord):
            # user didn't link their discord account

            return jsonify({
                'error': 'This user didn\'t link their Discord account'
            }), 402
        
        recovery_code = user.create_recovery_code() 
        if recovery_code:
            Discord.send_dm(discord_user_id=linked_discord.get('id'), content=f"""
We received a password recovery request for your kokot.host account
From IP: ||{get_real_ip()}||
**You may change your password using this link:** ||{get_real_host()}#!/recovery?recovery_code={recovery_code}||

**If you did not trigger this request, disregard this message**
""")

            return jsonify({
                'msg': 'The recovery link was sent to your linked Discord account'
            }), 200
        
    return jsonify({
        'error': 'Bad request'
    }), 400

@bp_backend.route('/user/recovery', methods=['POST'])
def user_recovery():
    if request.form:
        password = request.form.get('password')
        password_secondary = request.form.get('password_secondary')
        challenge = request.form.get('challenge')

        if not verify_cloudflare_challenge(challenge):
            # failed captcha

            return jsonify({
                'error': 'Captcha is required'
            }), 400
        
        if not password or not password_secondary:
            # no data provided

            return jsonify({
                'error': 'No password provided'
            }), 400
        
        if password != password_secondary:
            # passwords dont match

            return jsonify({
                'error': 'The passwords don\'t match'
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
        
        user = get_current_user()
        if not user and not is_ip_ratelimited(timedelta(minutes=1)):
            # resetting from recovery code?
            recovery_code = request.form.get('recovery_code')
            if recovery_code:
                user = next((u for u in User.get_all() if u.get_recovery_code() == recovery_code), None)

        if not user:
            return jsonify({
                'error': 'This link doesn\'t exist or has expired'
            }), 404
        
        user.clear_recovery_code()
        user.set_password(password=password)
    
        return jsonify({
            'msg': 'You have successfully changed your password'
        }), 200
    
    return jsonify({
        'error': 'Bad request'
    }), 400

@bp_backend.route('/user/register', methods=['POST'])
def user_register():
    if request.form:
        username = request.form.get('user')
        password = request.form.get('password')
        invite = request.form.get('invite')
        challenge = request.form.get('challenge')

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
            }), 404
        
        if User.from_username(username):
            # user already exists

            return jsonify({
                'error': 'Username is already taken'
            }), 400

        # success! lets create an user
        new_user = User.create(username=username, password=password, role=user_invite.role)
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

@bp_backend.route('/user/discord')
@require_access(level=UserRole.USER)
def user_discord():
    user = get_current_user()
    user_discord = user.get_discord_link()

    if user_discord:
        return jsonify(user_discord), 200

    return jsonify({
        'error': 'You haven\'t linked your Discord account yet'
    }), 204

@bp_backend.route('/user/link_discord')
@require_access(level=UserRole.USER)
def user_link_discord():
    if not (DISCORD_APP_CLIENT_ID and DISCORD_APP_CLIENT_SECRET):
        return jsonify({
            'error': 'This instance does not support Discord account linking'
        }), 400
    
    link = f'https://discord.com/oauth2/authorize?client_id={DISCORD_APP_CLIENT_ID}&response_type=code&redirect_uri={get_real_host()}api/user/link_discord_callback&integration_type=0&scope=guilds.join+identify'
    return redirect(link)

@bp_backend.route('/user/link_discord_callback')
@ratelimit(duration=timedelta(seconds=4))
@require_access(level=UserRole.USER)
def user_link_discord_callback():
    user = get_current_user()
    if user.get_discord_link():
        return jsonify({
            'error': 'You already linked your Discord account!'
        }), 409

    code = request.args.get('code')
    if code:
        linked_user_token = Discord.exchange_oauth_code(code=code, redirect_uri=f'{get_real_host()}api/user/link_discord_callback')

        if linked_user_token:
            linked_user_info = Discord.get_user_info(linked_user_token.get('access_token'))

            if linked_user_info:
                linked_user_id = linked_user_info.get('id')

                if linked_user_id:
                    linked_user_username = linked_user_info.get('username')
                    linked_user_headshot = f'https://cdn.discordapp.com/avatars/{linked_user_id}/{linked_user_info.get('avatar')}.webp'

                    # link user in db
                    user.set_linked_discord(discord_id=linked_user_id, discord_username=linked_user_username, discord_headshot=linked_user_headshot)

                    # make the user join our server
                    Discord.add_user_to_guild(DISCORD_SERVER_ID, linked_user_id, linked_user_token)

    return redirect('/')

@bp_backend.route('/user/unlink_discord', methods=['DELETE'])
@require_access(level=UserRole.USER)
def user_unlink_discord():
    if not (DISCORD_APP_CLIENT_ID and DISCORD_APP_CLIENT_SECRET):
        return jsonify({
            'error': 'This instance does not support discord account linking'
        }), 400
    
    user = get_current_user()
    user.set_linked_discord(discord_id=None, discord_username=None, discord_headshot=None)

    return jsonify({
        'msg': 'OK'
    }), 200

@bp_backend.route('/admin/generate_invite', methods=['POST'])
@require_access(level=UserRole.ADMIN)
def admin_generate_invite():
    invite = Invite.create(invite_key())

    if invite:
        return jsonify({
            'invite': invite.hash_
        }), 200

    return jsonify({
        'error': 'Bad request'
    }), 400

@bp_backend.route('/admin/purge_invites', methods=['POST'])
@require_access(level=UserRole.ADMIN)
def admin_purge_invites():
    deleted = 0

    for invite in Invite.get_all():
        if not invite.owner_id:
            invite.delete()
            deleted += 1

    return jsonify({
        'msg': f'Deleted {deleted} invite(s)'
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
            'join_date': user.get_join_date(),
            'role': user.role
        })
    
    return jsonify(result), 200
