import os
from datetime import datetime
from web.models.db import DB
from web.utils.networking import get_real_host

class File:
    def __init__(self, uri, path, filename, expires, mimetype, owner_id, size_mb, uploaded_at=None):
        self.uri = uri
        self.path = path
        self.filename = filename
        self.expires = expires
        self.mimetype = mimetype
        self.owner_id = owner_id
        self.size_mb = size_mb
        self.uploaded_at = uploaded_at

    # cursor.execute('SELECT path, filename, expires, mimetype, owner_id, size_mb, uploaded_at FROM files WHERE uri = ?', (target_key,))

    @staticmethod
    def from_uri(uri):
        uri = uri.replace('.gif', '')

        with DB.get().cursor() as cursor:
            cursor.execute('SELECT path, filename, expires, mimetype, owner_id, size_mb, uploaded_at FROM files WHERE uri = ?', (uri,))
            result = cursor.fetchone()
            if result:
                path, filename, expires, mimetype, owner_id, size_mb, uploaded_at = result
                file = File(uri=uri, path=path, filename=filename, expires=expires, mimetype=mimetype, owner_id=owner_id, size_mb=size_mb, uploaded_at=uploaded_at)

                if expires and datetime.strptime(expires, '%Y-%m-%d %H:%M:%S') < datetime.now():
                    file.delete()
                    return None
                
                return file

    @staticmethod
    def upload(uploader, filename, uri, path, size_mb, mimetype, expires):
        uploader_id = uploader.uid

        with DB.get().cursor() as cursor:
            cursor.execute(
                'INSERT INTO files (owner_id, filename, path, uri, size_mb, mimetype, expires) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (uploader_id, filename, path, uri, size_mb, mimetype, expires)
            )

            return File(uri=uri, path=path, filename=filename, expires=expires, mimetype=mimetype, owner_id=uploader_id, size_mb=size_mb)

    def delete(self):
        os.remove(self.path)
        with DB.get().cursor() as cursor:
            cursor.execute(
                'DELETE FROM files WHERE uri = ?',
                (self.uri,)
            )

    def modify(self, new_filename=None):
        if new_filename:
            with DB.get().cursor() as cursor:
                cursor.execute(
                    'UPDATE files SET filename=? WHERE uri=?',
                    (new_filename, self.uri,)
                )

    def get_thumbnail(self):
        return 'image' in self.mimetype and self.get_url() or '/static/images/no-preview.png'

    def get_url(self):
        return f'{get_real_host()}uploads/{self.uri}{self.mimetype.endswith('gif') and '.gif' or ''}'
    
    def get_url_raw(self):
        return f'{get_real_host()}/files/uploads/{self.uri}{self.mimetype.endswith('gif') and '.gif' or ''}'
    
    def get_deletion_url(self):
        return f'{get_real_host()}files/delete?uri={self.uri}'