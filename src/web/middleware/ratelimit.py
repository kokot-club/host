from flask import request, abort
from datetime import datetime
from functools import wraps
from web.utils.networking import get_real_ip

connections = {}

def log_ip_event():
    path = request.path
    if not path:
        return

    ip = get_real_ip()
    if not ip:
        return
    
    connections[path][ip] = datetime.now()

def is_ip_ratelimited(duration):
    path = request.path
    if not path:
        return False
    
    if not connections.get(path):
        connections[path] = {}

    ip = get_real_ip()
    if not ip:
        return False
    
    last = connections[path].get(ip)
    if not last or datetime.now() - duration > last:
        log_ip_event()
        return False

    return True

def ratelimit(duration):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if is_ip_ratelimited(duration):
                return abort(429)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator