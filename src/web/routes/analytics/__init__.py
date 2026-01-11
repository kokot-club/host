from flask import Blueprint, request, make_response, redirect, jsonify
from datetime import datetime
from shared.models import UserRole
from shared.auth import require_access, uid_to_username
from shared.db import DB

bp_analytics = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp_analytics.route('/userbase_info')
@require_access(level=UserRole.USER)
def userbase_info(max_days=7):
    result = {
        'latest_user': 0,
        'latest_uid': 0,
        'total_users': 0,
        'history': {
            'labels': [],
            'data': []
        }
    }

    with DB.get().cursor() as cursor:
        now = datetime.now().timestamp()
        for tick in range(max_days, -1, -1):
            timestamp: float = now - tick * 60 * 60 * 24
            timestamp_str: str = datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y')

            cursor.execute(
                'SELECT MAX(id), username FROM users WHERE UNIXEPOCH(join_date)<=?',
                (timestamp,)
            )
            record = cursor.fetchone()
            if record and all(record):
                if tick == 0:
                    result['latest_uid'] = record[0]
                    result['latest_user'] = uid_to_username(record[0])
                    result['total_users'] = record[0]

                result['history']['data'].append(record[0])
            else:
                result['history']['data'].append(0)

            result['history']['labels'].append(timestamp_str)

    return jsonify(result), 200

@bp_analytics.route('/server_storage')
@require_access(level=UserRole.USER)
def server_storage():
    with DB.get().cursor() as cursor:
        cursor.execute('SELECT SUM(size_mb), COUNT(*) FROM files')
        restult = cursor.fetchone()

        return jsonify({
            'used_mb': restult[0],
            'total_uploads': restult[1]
        }), 200
    
    return jsonify({
        'error': 'Bad request'
    }), 401

@bp_analytics.route('/daily_uploads')
@require_access(level=UserRole.USER)
def uploads_daily(max_days=7):
    result = {
        'labels': [],
        'data': []
    }

    with DB.get().cursor() as cursor:
        now = datetime.now().timestamp()
        for tick in range(max_days - 1, -1, -1):
            timestamp: float = now - tick * 60 * 60 * 24
            timestamp_str: str = datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y')

            cursor.execute(
                'SELECT COUNT(*) FROM files WHERE DATE(uploaded_at) = DATE(?,"unixepoch")',
                (timestamp,)
            )
            record = cursor.fetchone()

            result['labels'].append(timestamp_str)
            result['data'].append(record[0] if record else 0)

    return jsonify(result), 200