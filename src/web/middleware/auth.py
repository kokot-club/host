import os
from flask import request, jsonify, make_response, redirect
from itsdangerous import URLSafeSerializer
from functools import wraps
from datetime import datetime, timedelta
from web.models.db import DB
from web.models.user import User
from web.models.role import UserRole

SECRET = os.environ.get('SECRET')
if not SECRET:
    raise RuntimeError('SECRET environment variable is required')

serializer = URLSafeSerializer(SECRET)

def set_user_cookie(user_data, response): 
    response.set_cookie('auth', serializer.dumps(user_data), httponly=False, secure=True, samesite='Lax', expires=datetime.now() + timedelta(days=30))
    return response

def clear_user_cookie(response):
    response.delete_cookie('auth', httponly=False, secure=True, samesite='Lax')
    return response

def get_current_user() -> User | None:
    auth_cookie = request.cookies.get('auth')
    if not auth_cookie:
        api_key = request.headers.get('X-Api-Key')
        if api_key:
            with DB.get().cursor() as cursor:
                cursor.execute('SELECT id, username, role FROM users WHERE api_key = ?', (api_key,))
                result = cursor.fetchone()
                if result:
                    uid, *_ = result

                    user = User.from_uid(uid)
                    if user:
                        user.is_api = True
                        return user

                return None

        return None

    user_data = serializer.loads(auth_cookie)
    if user_data:
        user_uid = user_data.get('uid')
        if user_uid:
            return User.from_uid(user_uid)
    
    return None
    
def user_has_access(level):
    user = get_current_user()
    if not user or user.role < level.value:
        return False
    
    return True

def require_access(level: UserRole, api_keys=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or user.is_banned():
                # invalid cookie or the user is banned
                return clear_user_cookie(make_response(redirect('/'), 403))

            if (not user or user.role is None or user.role < level.value or (user.is_api and not api_keys)):
                return jsonify({
                    'error': 'Not authorized'
                }), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
