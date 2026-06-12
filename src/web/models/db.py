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
        def attempt_query(cursor, query):
            try:
                cursor.execute(query)
            except sqlite3.OperationalError: pass

        with self.cursor() as cursor:
            # users
            cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT)")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN join_date DATE NOT NULL DEFAULT CURRENT_TIMESTAMP")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN username TEXT NOT NULL UNIQUE")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN password TEXT NOT NULL")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN role INTEGER NOT NULL")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN api_key TEXT UNIQUE")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN fixed_storage_mb FLOAT")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN linked_discord_id INTEGER UNIQUE")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN linked_discord_username TEXT")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN linked_discord_headshot TEXT")
            attempt_query(cursor, "ALTER TABLE users ADD COLUMN banned BOOL DEFAULT 0")

            # settings
            cursor.execute("CREATE TABLE IF NOT EXISTS settings (user_id INTEGER NOT NULL UNIQUE)")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN external_css TEXT DEFAULT ''")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN anonymous BOOL NOT NULL DEFAULT 0")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN auto_expire FLOAT NOT NULL DEFAULT 0")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN embed_color VARCHAR(7)")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN embed_title VARCHAR(40) DEFAULT ''")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN embed_description VARCHAR(200) DEFAULT ''")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN embed_sitename VARCHAR(200) DEFAULT ''")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN embed_siteurl VARCHAR(200) DEFAULT ''")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN embed_authorname VARCHAR(200) DEFAULT ''")
            attempt_query(cursor, "ALTER TABLE settings ADD COLUMN embed_authorurl VARCHAR(200) DEFAULT ''")

            # invites
            cursor.execute("CREATE TABLE IF NOT EXISTS invites (hash TEXT PRIMARY KEY NOT NULL)")
            attempt_query(cursor, "ALTER TABLE invites ADD COLUMN role INTEGER NOT NULL DEFAULT 0")
            attempt_query(cursor, "ALTER TABLE invites ADD COLUMN user_id INTEGER UNIQUE")

            # files
            cursor.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT)")
            attempt_query(cursor, "ALTER TABLE files ADD COLUMN owner_id INTEGER NOT NULL")
            attempt_query(cursor, "ALTER TABLE files ADD COLUMN uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
            attempt_query(cursor, "ALTER TABLE files ADD COLUMN filename VARCHAR(150) NOT NULL")
            attempt_query(cursor, "ALTER TABLE files ADD COLUMN path TEXT NOT NULL")
            attempt_query(cursor, "ALTER TABLE files ADD COLUMN uri TEXT NOT NULL")
            attempt_query(cursor, "ALTER TABLE files ADD COLUMN size_mb FLOAT NOT NULL")
            attempt_query(cursor, "ALTER TABLE files ADD COLUMN mimetype STRING NOT NULL")
            attempt_query(cursor, "ALTER TABLE files ADD COLUMN expires DATETIME")
            attempt_query(cursor, "ALTER TABLE files ADD COLUMN views INTEGER NOT NULL DEFAULT 0")

            # folders
            cursor.execute("CREATE TABLE IF NOT EXISTS folders (id INTEGER PRIMARY KEY AUTOINCREMENT)")
            attempt_query(cursor, "ALTER TABLE folders ADD COLUMN name TEXT NOT NULL")

            # insert initial invite if table empty
            cursor.execute('SELECT 1 FROM invites')
            if not cursor.fetchone():
                invite = os.environ.get('SETUP_INVITE')
                cursor.execute('INSERT INTO invites (hash, role) VALUES (?, 2)', (invite,))

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
