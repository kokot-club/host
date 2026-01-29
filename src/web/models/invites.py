from web.models.db import DB
from web.models.role import UserRole

class Invite:
    def __init__(self, hash_, owner_id=None, role=UserRole.USER.value):
        self.hash_ = hash_
        self.owner_id = owner_id
        self.role = role

    @staticmethod
    def create(hash_, role=UserRole.USER.value):
        with DB.get().cursor() as cursor:
            cursor.execute('INSERT INTO invites (hash, user_id, role) VALUES (?, NULL, ?)', (hash_, role,))

            return Invite(hash_=hash_, role=role)
    
    @staticmethod
    def get_all():
        result = []

        with DB.get().cursor() as cursor:
            cursor.execute('SELECT hash FROM invites')
            for (hash_,) in cursor.fetchall():
                result.append(Invite.from_hash(hash_))

        return result

    @staticmethod
    def from_hash(hash_):
        with DB.get().cursor() as cursor:
            cursor.execute('SELECT hash, user_id, role FROM invites WHERE hash = ?', (hash_,))
            
            result = cursor.fetchone()
            if result:
                hash_, owner_id, role = result

                return Invite(hash_=hash_, owner_id=owner_id, role=role)

    def set_claimed(self, user_id):
        with DB.get().cursor() as cursor:
            cursor.execute(
                'UPDATE invites SET user_id = ? WHERE hash = ?',
                (user_id, self.hash_,)
            )

    def delete(self):
        with DB.get().cursor() as cursor:
            cursor.execute('DELETE FROM invites WHERE user_id IS NULL')