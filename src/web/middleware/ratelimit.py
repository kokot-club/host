import threading
from flask import request, jsonify
from datetime import datetime, timedelta
from functools import wraps
from web.utils.networking import get_real_ip

connections = {}
_lock = threading.Lock()
CLEANUP_INTERVAL = timedelta(seconds=60)

def _cleanup():
    now = datetime.now()
    stale_paths = []
    for path, ips in connections.items():
        stale_ips = [ip for ip, ts in ips.items() if now - ts > CLEANUP_INTERVAL]
        for ip in stale_ips:
            del ips[ip]
        if not ips:
            stale_paths.append(path)
    for path in stale_paths:
        del connections[path]

def log_ip_event():
    path = request.path
    if not path:
        return

    ip = get_real_ip()
    if not ip:
        return

    with _lock:
        if path not in connections:
            connections[path] = {}
        connections[path][ip] = datetime.now()

def is_ip_ratelimited(duration):
    path = request.path
    if not path:
        return False

    ip = get_real_ip()
    if not ip:
        return False

    with _lock:
        if path not in connections:
            connections[path] = {}

        last = connections[path].get(ip)
        if not last or datetime.now() - duration > last:
            connections[path][ip] = datetime.now()
            _cleanup()
            return False

        return True

def ratelimit(duration):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if is_ip_ratelimited(duration):
                return jsonify({
                    'error': 'You are being ratelimited'
                }), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator