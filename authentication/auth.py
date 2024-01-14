import binascii
import hashlib
import os
from pathlib import Path

import config
from utils.singleton import Singleton
from .user import User


class Auth(metaclass=Singleton):
    """Class for authentication process

    Raises:
        AuthExceptions.UserNotExistException: When user does not exist
        AuthExceptions.PasswordIncorrectException: When password is incorrect

    Returns:
        bool: True if user is authenticated
    """

    def __init__(self):
        self.passwd_file_path = Path(config.PASSWD_FILE_PATH).expanduser()
        self.__salt = self._generate_salt()

    def __str__(self) -> str:
        return f"""
            Auth module
            \n----------------\n
            Passwd file path: {self.passwd_file_path}\n
            """

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user

        Args:
            username (str): string with username
            password (str): string with password

        Raises:
            AuthExceptions.UserNotExistException: when user does not exist
            AuthExceptions.PasswordIncorrectException: when password is incorrect

        Returns:
            bool: True if user is authenticated
        """

        if not self._user_exists(username):
            return False

        if not self._is_password_correct(username, password):
            return False

        return True

    def _user_exists(self, username: str) -> bool:
        """Check if user exist in passwd file

        Args:
            username (str): string with username

        Returns:
            bool: True if user exist
        """

        for user in self._get_users():
            if user.username == username:
                return True

        return False
    
    def _is_password_correct(self, username: str, password: str) -> bool:
        """Check if password is correct

        Args:
            username (str): string with username
            password (str): string with password

        Returns:
            bool: True if password is correct
        """

        for user in self._get_users():
            if user.username == username and user.password == self._hash_password(password):
                return True

        return False

    def _hash_password(self, password: str) -> str:
        """Hash password with sha256

        Args:
            password (str): string with password

        Returns:
            str: hashed password
        """

        return hashlib.sha256((password + self.__salt).encode('utf-8')).hexdigest()

    def _generate_salt(self) -> str:
        """Generate salt for password hashing

        Returns:
            str: salt
        """

        return binascii.hexlify(os.urandom(16)).decode('utf-8')
    
    def _get_users(self) -> list[User]:
        """Get users from passwd file

        Returns:
            list[tuple[str, str]]: list of users
        """

        users = []

        with open(self.passwd_file_path) as passwd_file:
            for line in passwd_file:
                username, password = line.strip().split(':')
                users.append(User(username, password))

        return users
    
    def create_passwd_file(self) -> None:
        """Create passwd file if not exist"""

        path = Path(config.PASSWD_FILE_PATH).expanduser()

        # If file exists, clear it - else, create it
        if path.stat().st_size > 0:
            open(path, 'w').close()
        else:
            path.touch()

        # Write users to file
        with open(path, 'w') as passwd_file:
            for user in config.USERS:
                passwd_file.write(f"{user.username}:{self._hash_password(user.password)}\n")
