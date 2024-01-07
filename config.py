import os

from pathlib import Path
from dotenv import load_dotenv
from authentication.Auth import Auth
from authentication.User import User

load_dotenv()

# Add users here
admin = User("admin", "admin")
user1 = User("user-1", "user-1")
user2 = User("user-2", "user-2")
user3 = User("user-3", "user-3")

users = [admin, user1, user2, user3]

# Create file with users
def create_passwd_file(auth: Auth) -> None:

    # If file exists, clear it - else, create it
    if Path(os.getenv('PASSWD_FILE_PATH')).expanduser().stat().st_size > 0:
        open(Path(os.getenv('PASSWD_FILE_PATH')).expanduser(), "w").close()
    else:
        Path(os.getenv('PASSWD_FILE_PATH')).expanduser().touch()

    # Write users to file
    with open(Path(os.getenv('PASSWD_FILE_PATH')).expanduser(), "w") as passwdFile:
        for user in users:
            passwdFile.write(f"{user.username}:{auth.hashPassword(user.password)}\n")
