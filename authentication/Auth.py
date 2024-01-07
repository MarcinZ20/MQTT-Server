import binascii
import hashlib
import os

from pathlib import Path
from exceptions.authentication import (PasswdFileNotExistException,
                                       PasswordIncorrectException,
                                       UserNotExistException)


class Auth:
    """Class for authentication process

    Args:
        passwdFilePath (str, optional): path to passwd file. Defaults to None.

    Raises:
        AuthExceptions.UserNotExistException: When user does not exist
        AuthExceptions.PasswordIncorrectException: When password is incorrect

    Returns:
        bool: True if user is authenticated
    """

    def __init__(self, passwdFilePath: str = None):
        self.passwdFilePath = Path(passwdFilePath).expanduser()
        self.__salt = self.__generateSalt()

    def __str__(self) -> str:
        return f"""
            Auth module
            \n----------------\n
            Passwd file path: {self.passwdFilePath}\n
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
        if not self.__isUserExist(username):
            raise UserNotExistException(username)

        if not self.__isPasswordCorrect(username, password):
            raise PasswordIncorrectException(username)

        return True
    
    def __isUserExist(self, username: str) -> bool:
        """Check if user exist in passwd file

        Args:
            username (str): string with username

        Returns:
            bool: True if user exist
        """
        with open(self.passwdFilePath, 'r') as passwdFile:
            for line in passwdFile:
                if line.startswith(username):
                    return True
        return False
    
    def __isPasswordCorrect(self, username: str, password: str) -> bool:
        """Check if password is correct

        Args:
            username (str): string with username
            password (str): string with password

        Returns:
            bool: True if password is correct
        """
        with open(self.passwdFilePath, 'r') as passwdFile:
            for line in passwdFile:
                if line.startswith(username):
                    hashedPassword = line.split(':')[1]
                    return self.hashPassword(password) == hashedPassword
        return False

    def hashPassword(self, password: str) -> str:
        """Hash password with sha256

        Args:
            password (str): string with password

        Returns:
            str: hashed password
        """
        return hashlib.sha256((password + self.__salt).encode('utf-8')).hexdigest()

    def __generateSalt(self) -> str:
        """Generate salt for password hashing

        Returns:
            str: salt
        """
        return binascii.hexlify(os.urandom(16)).decode('utf-8')
    
    def get_users(self) -> list[tuple[str, str]]:
        """Get users from passwd file

        Returns:
            list[tuple[str, str]]: list of users
        """
        users = []
        
        with open(self.passwdFilePath, 'r') as passwdFile:
            for line in passwdFile:
                username = line.split(':')[0]
                password = line.split(':')[1]
                users.append((username, password))
        return users
