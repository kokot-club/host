from flask import Blueprint, jsonify
from datetime import datetime
from web.middleware.auth import require_access
from web.models.db import DB
from web.models.user import User
from web.models.role import UserRole

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
                'SELECT MAX(id), username FROM users WHERE UNIXEPOCH(join_date) <= ?',
                (timestamp,)
            )
            record = cursor.fetchone()
            if record:
                user_id, username = record
                user = User.from_uid(user_id)
                display_name = user.get_display_name()

                if tick == 0:
                    result['latest_uid'] = user_id
                    result['latest_user'] = display_name
                    result['total_users'] = user_id

                result['history']['data'].append(user_id)
            else:
                result['history']['data'].append(0)

            result['history']['labels'].append(timestamp_str)

    return jsonify(result), 200

@bp_analytics.route('/server_storage')
@require_access(level=UserRole.USER)
def server_storage():
    return jsonify({
        'used_mb': sum(u.get_storage_usage_mb() for u in User.get_all()),
        'total_uploads': sum(len(u.get_uploaded_files()) for u in User.get_all())
    }), 200

@bp_analytics.route('/daily_uploads')
@require_access(level=UserRole.USER)
def uploads_daily(max_days=7):
    result = {
        'labels': [],
        'data': []
    }

    with DB.get().cursor() as cursor:
        now = datetime.now().timestamp()
        for tick in range(max_days, -1, -1):
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