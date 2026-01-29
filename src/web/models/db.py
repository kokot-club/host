import sqlite3
import os
import threading
from contextlib import contextmanager

class DB:
    _local = threading.local()

    @staticmethod
    def get():
        if not hasattr(DB._local, 'db'):
            DB._local.db = DB()

        return DB._local.db

    def __init__(self) -> None:
        os.makedirs(os.path.join(os.getcwd(), 'db'), exist_ok=True)
        self._conn = sqlite3.connect('db/instance.db', autocommit=True, check_same_thread=False)

    def run(self):
        def add_column_if_missing(cursor, table, column, col_type):
            cursor.execute(f'PRAGMA table_info("{table}")')
            cols = [c[1] for c in cursor.fetchall()]
            if column not in cols:
                base_type = col_type.replace('UNIQUE', '').replace('NOT NULL', '').strip()
                cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {base_type}')
                if 'UNIQUE' in col_type:
                    cursor.execute(f'CREATE UNIQUE INDEX IF NOT EXISTS idx_{table}_{column} ON {table}({column})')

        with self.cursor() as cursor:
            # users
            cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT)")
            add_column_if_missing(cursor, 'users', 'join_date', 'DATE NOT NULL DEFAULT CURRENT_TIMESTAMP')
            add_column_if_missing(cursor, 'users', 'username', 'TEXT NOT NULL UNIQUE')
            add_column_if_missing(cursor, 'users', 'password', 'TEXT NOT NULL')
            add_column_if_missing(cursor, 'users', 'role', 'INTEGER NOT NULL')
            add_column_if_missing(cursor, 'users', 'api_key', 'TEXT UNIQUE')
            add_column_if_missing(cursor, 'users', 'fixed_storage_mb', 'FLOAT')

            # settings
            cursor.execute("CREATE TABLE IF NOT EXISTS settings (user_id INTEGER NOT NULL UNIQUE)")
            add_column_if_missing(cursor, 'settings', 'external_css', 'TEXT DEFAULT ""')
            add_column_if_missing(cursor, 'settings', 'anonymous', 'BOOL NOT NULL DEFAULT 0')
            add_column_if_missing(cursor, 'settings', 'auto_expire', 'FLOAT NOT NULL DEFAULT 0')
            add_column_if_missing(cursor, 'settings', 'embed_color', 'VARCHAR(7)')
            add_column_if_missing(cursor, 'settings', 'embed_title', 'VARCHAR(40) DEFAULT ""')
            add_column_if_missing(cursor, 'settings', 'embed_description', 'VARCHAR(200) DEFAULT ""')
            add_column_if_missing(cursor, 'settings', 'embed_sitename', 'VARCHAR(200) DEFAULT ""')
            add_column_if_missing(cursor, 'settings', 'embed_siteurl', 'VARCHAR(200) DEFAULT ""')
            add_column_if_missing(cursor, 'settings', 'embed_authorname', 'VARCHAR(200) DEFAULT ""')
            add_column_if_missing(cursor, 'settings', 'embed_authorurl', 'VARCHAR(200) DEFAULT ""')

            # invites
            cursor.execute("CREATE TABLE IF NOT EXISTS invites (hash TEXT PRIMARY KEY NOT NULL)")
            add_column_if_missing(cursor, 'invites', 'role', 'INTEGER NOT NULL DEFAULT 0')
            add_column_if_missing(cursor, 'invites', 'user_id', 'INTEGER UNIQUE')

            # files
            cursor.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT)")
            add_column_if_missing(cursor, 'files', 'owner_id', 'INTEGER NOT NULL')
            add_column_if_missing(cursor, 'files', 'uploaded_at', 'DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP')
            add_column_if_missing(cursor, 'files', 'filename', 'VARCHAR(150) NOT NULL')
            add_column_if_missing(cursor, 'files', 'path', 'TEXT NOT NULL')
            add_column_if_missing(cursor, 'files', 'uri', 'TEXT NOT NULL')
            add_column_if_missing(cursor, 'files', 'size_mb', 'FLOAT NOT NULL')
            add_column_if_missing(cursor, 'files', 'mimetype', 'STRING NOT NULL')
            add_column_if_missing(cursor, 'files', 'expires', 'DATETIME')
            add_column_if_missing(cursor, 'files', 'views', 'INTEGER NOT NULL DEFAULT 0')

            # folders
            cursor.execute("CREATE TABLE IF NOT EXISTS folders (id INTEGER PRIMARY KEY AUTOINCREMENT)")
            add_column_if_missing(cursor, 'folders', 'name', 'TEXT NOT NULL')

            # insert initial invite if table empty
            cursor.execute('SELECT 1 FROM invites')
            if not cursor.fetchone():
                invite = os.environ.get('SETUP_INVITE')
                self._conn.execute('INSERT INTO invites (hash, role) VALUES (?, 2)', (invite,))

    def connection(self):
        return self._conn

    @contextmanager
    def cursor(self):
        cursor = self.connection().cursor()

        try:
            yield cursor
        finally:
            cursor.close()
        
    def close(self):
        self.connection().close()
