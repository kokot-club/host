import os
import requests
import datetime
from flask import abort, request, redirect
from functools import wraps
from itsdangerous import URLSafeSerializer
from .db import DB
from .models import User, UserRole

SECRET = os.environ.get('SECRET')
if not SECRET:
    raise RuntimeError('SECRET environment variable is required')

CLOUDFLARE_TURNSTILE_SECRET = os.environ.get('CLOUDFLARE_TURNSTILE_SECRET')
if not CLOUDFLARE_TURNSTILE_SECRET:
    print('Turnstile is off')

serializer = URLSafeSerializer(SECRET)

# nginx helpers
def get_real_host():
    x_host = request.headers.get('X-Host')
    return x_host and f'https://{x_host}/' or request.host_url

def get_real_ip():
    x_real_ip = request.headers.get('X-Real-IP') or request.headers.get('X-Real-Ip')
    return x_real_ip or request.remote_addr

def uid_to_username(uid):
    user_settings = get_user_settings(uid)
    if user_settings.get('anonymous', False) == True:
        return '████████'

    with DB.get().cursor() as cursor:
        cursor.execute('SELECT username FROM users WHERE id = ?', (uid,))
        result = cursor.fetchone()
        if result:
            return result[0]

        return None

def get_current_user() -> User | None:
    auth_cookie = request.cookies.get('auth')
    if not auth_cookie:
        api_key = request.headers.get('X-Api-Key')
        if api_key:
            with DB.get().cursor() as cursor:
                cursor.execute('SELECT id, username, role FROM users WHERE api_key = ?', (api_key,))
                result = cursor.fetchone()
                if result:
                    return User(uid=result[0], username=result[1], role=UserRole(result[2]), is_api=True)

                return None

        return None
    
    try:
        user = User(**serializer.loads(auth_cookie))
        user.role = UserRole(user.role)

        return user
    except Exception:
        # invalid cookie
        return None
    
def get_user_upload_key():
    user = get_current_user()
    if user:
        with DB.get().cursor() as cursor:
            cursor.execute(
                'SELECT api_key FROM users WHERE id = ?',
                (user.uid,)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            
    return None
            
def set_user_upload_key(upload_key):
    user = get_current_user()
    if user:
        with DB.get().cursor() as cursor:
            cursor.execute('UPDATE users SET api_key = ? WHERE id = ?', (upload_key, user.uid))
            if cursor.rowcount > 0:
                return True
            
    return False
    
def get_user_settings(user_id=-1):
    with DB.get().cursor() as cursor:
        cursor.execute(
            'SELECT * FROM settings WHERE user_id = ?',
            (user_id,)
        )
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows][0]

    return None

def verify_cloudflare_challenge(challenge_token):
    if CLOUDFLARE_TURNSTILE_SECRET:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={'secret': CLOUDFLARE_TURNSTILE_SECRET, 'response': challenge_token}
        )
        print(response.json())
        if response and response.json():
            return response.json().get('success', False)
        
        return False
    
    # protection is off
    return True

def require_access(level: UserRole, api_keys=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                # invalid cookie
                return redirect('/api/user/logout')

            if not user or user.role.value < level.value or (user.is_api == True and api_keys == False):
                return abort(403)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def set_user_cookie(user_data, response): 
    response.set_cookie('auth', serializer.dumps(user_data), httponly=False, secure=True, samesite='Strict', expires=datetime.datetime.now() + datetime.timedelta(days=30))
    return response

def clear_user_cookie(response):
    response.delete_cookie('auth', httponly=False, secure=True, samesite='Strict')
    return response