from werkzeug.security import generate_password_hash, check_password_hash
from web.models.db import DB
from web.models.role import UserRole
from web.models.files import File

class User:
    def __init__(self, uid, username, role, is_api=False):
        self.uid = uid
        self.username = username
        self.role = role
        self.is_api = is_api

    @staticmethod
    def create(username, password, role=UserRole.USER.value):
        password_hash = generate_password_hash(password)

        with DB.get().cursor() as cursor:
            cursor.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                (username, password_hash, role)
            )

            new_user_id = cursor.lastrowid
            cursor.execute(
                'INSERT INTO settings (user_id) VALUES (?)',
                (new_user_id,)
            ),
    
            return User(uid=new_user_id, username=username, role=role)
    
    @staticmethod
    def get_all():
        result = []

        with DB.get().cursor() as cursor:
            cursor.execute('SELECT id FROM users')
            for (uid,) in cursor.fetchall():
                result.append(User.from_uid(uid))

        return result
    
    @staticmethod
    def from_uid(uid):
        with DB.get().cursor() as cursor:
            cursor.execute(
                'SELECT username, role FROM users WHERE id = ?',
                (uid,)
            ),

            result = cursor.fetchone()
            if result:
                username, role = result
                return User(uid=uid, username=username, role=role)

    @staticmethod
    def from_username(username):
        with DB.get().cursor() as cursor:
            cursor.execute(
                'SELECT id, role FROM users WHERE username = ?',
                (username.lower(),)
            ),

            result = cursor.fetchone()
            if result:
                uid, role = result
                return User(uid=uid, username=username, role=role)
            
    def password_matches_hash(self, password):
        with DB.get().cursor() as cursor:
            cursor.execute(
                'SELECT password FROM users WHERE id = ?',
                (self.uid,)
            )

            result = cursor.fetchone()
            if result:
                password_hash = result[0]
                return check_password_hash(password_hash, password)

    def get_settings(self):
        with DB.get().cursor() as cursor:
            cursor.execute(
                'SELECT * FROM settings WHERE user_id = ?',
                (self.uid,)
            )

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows][0]

        return None
    
    def set_settings(self, settings_data):
        def is_hex(hex_str):
            if hex_str.startswith('#') and len(hex_str) == 7:
                return hex_str
            
            return '#000000'

        def is_url(url_str):
            if url_str.startswith(('http://', 'https://')):
                return url_str
            
            return ''

        fields = {
            'embed_color': lambda v: is_hex(v),
            'embed_title': lambda v: v[:40],
            'embed_sitename': lambda v: v[:40],
            'embed_siteurl': lambda v: is_url(v)[:100],
            'embed_authorname': lambda v: v[:200],
            'embed_authorurl': lambda v: is_url(v)[:100],
            'embed_description': lambda v: v[:200],
            'anonymous': lambda v: str(v).lower() == 'true',
            'auto_expire': lambda v: min(max(int(v), 0), 604800),
        }

        set_clauses = []
        values = []

        for key, transform in fields.items():
            if key in settings_data:
                set_clauses.append(f'{key} = ?')
                values.append(transform(settings_data[key]))

                if not set_clauses:
                    return

                values.append(self.uid)

                with DB.get().cursor() as cursor:
                    cursor.execute(
                        f"""
                        UPDATE settings
                        SET {', '.join(set_clauses)}
                        WHERE user_id = ?
                        """,
                        values
                    )

    def set_api_key(self, api_key):
        with DB.get().cursor() as cursor:
            cursor.execute('UPDATE users SET api_key = ? WHERE id = ?', (api_key, self.uid))
            if cursor.rowcount > 0:
                return True
            
        return False

    def get_api_key(self):
        with DB.get().cursor() as cursor:
            cursor.execute(
                'SELECT api_key FROM users WHERE id = ?',
                (self.uid,)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            
        return None

    def get_uploaded_files(self, query='%', max_files=9999999, offset=0):
        result = []

        with DB.get().cursor() as cursor:
            cursor.execute(
                'SELECT uri FROM files WHERE owner_id = ? AND filename LIKE ? ORDER BY uploaded_at DESC LIMIT ? OFFSET ?',
                (self.uid, query, max_files, offset)
            )
            for (uri,) in cursor.fetchall():
                file = File.from_uri(uri)
                if file:
                    result.append(file)

        return result

    def get_storage_usage_mb(self):
        return sum([f.size_mb for f in self.get_uploaded_files()])

    def get_storage_space_mb(self):
        return 10000
    
    def get_display_name(self):
        return self.username