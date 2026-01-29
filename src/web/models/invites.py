from web.models.db import DB

class Invite:
    def __init__(self, hash_):
        self.hash_ = hash_

    @staticmethod
    def create(hash_):
        with DB.get().cursor() as cursor:
            cursor.execute('INSERT INTO invites VALUES (?, NULL)', (hash_,))

            return Invite(hash_=hash_)
    
    @staticmethod
    def get_all():
        pass

    @staticmethod
    def from_hash(hash_):
        with DB.get().cursor() as cursor:
            cursor.execute('SELECT 1 FROM invites WHERE hash = ? AND user_id IS NULL', (hash_,))
            
            result = cursor.fetchone
            if result:
                return Invite(hash_=result[0])

    def set_claimed(self, user_id):
        pass

    def delete(self):
        pass