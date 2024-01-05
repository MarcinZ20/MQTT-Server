import hashlib
import binascii
import os 

from authentication import AuthConfig, AuthExceptions


class Auth:
    """Class for authentication process

    Raises:
        AuthExceptions.UserNotExistException: When user does not exist
        AuthExceptions.PasswordIncorrectException: When password is incorrect

    Returns:
        _type_: _description_
    """

    __passwdFilePath = None
    __salt = None

    def __init__(self):
        self.__passwdFilePath = AuthConfig.getPasswdFilePath()
        self.__salt = self.__generateSalt()

    def __str__(self) -> str:
        return f"""
            Auth module
            \n----------------\n
            Passwd file path: {self.__passwdFilePath}
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
            raise AuthExceptions.UserNotExistException(username)

        if not self.__isPasswordCorrect(username, password):
            raise AuthExceptions.PasswordIncorrectException(username)

        return True
    
    def __isUserExist(self, username: str) -> bool:
        """Check if user exist in passwd file

        Args:
            username (str): string with username

        Returns:
            bool: True if user exist
        """
        with open(self.__passwdFilePath, 'r') as passwdFile:
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
        with open(self.__passwdFilePath, 'r') as passwdFile:
            for line in passwdFile:
                if line.startswith(username):
                    hashedPassword = line.split(':')[2]
                    return self.__hashPassword(password) == hashedPassword
        return False

    def __hashPassword(self, password: str) -> str:
        """Hash password with sha256

        Args:
            password (str): string with password
            salt (str): string with salt

        Returns:
            str: hashed password
        """
        return hashlib.sha256((password + self.salt).encode('utf-8')).hexdigest()

    def __generateSalt(self) -> str:
        """Generate salt for password hashing

        Returns:
            str: salt
        """
        return binascii.hexlify(os.urandom(16)).decode('utf-8')
    
    def __getHashedPassword(self, username: str) -> str:
        """Get hashed password from passwd file

        Args:
            username (str): string with username

        Returns:
            str: hashed password
        """
        with open(self.__passwdFilePath, 'r') as passwdFile:
            for line in passwdFile:
                if line.startswith(username):
                    return line.split(':')[2]
        return None
    