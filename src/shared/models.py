from enum import Enum
from dataclasses import dataclass

class UserRole(Enum):
    GUEST = -1
    USER = 0
    ADMIN = 1
    OWNER = 2

@dataclass
class User:
    uid: int
    username: str
    role: UserRole
    is_api: bool = False