from authentication.user import User

__all__ = (
    'PASSWD_FILE_PATH',
    'USERS'
)

PASSWD_FILE_PATH = '~/.mqtt_passwd'

USERS = [
    User('admin', 'admin'),
    User('user-1', 'user-1'),
    User('user-2', 'user-2'),
    User('user-3', 'user-3')
]
