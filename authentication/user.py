from dataclasses import dataclass

@dataclass
class User:
    username: str
    password: str

    def __str__(self):
        return f"{self.username}:{self.password}"

    def __repr__(self):
        return f"{self.username} {self.password}"
