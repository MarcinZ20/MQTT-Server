from abc import ABC, abstractmethod


class Client(ABC):
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    @abstractmethod
    def notify(self, message: str):
        pass

    @abstractmethod
    def publish(self, topic_structure: str, message: str):
        pass

    @abstractmethod
    def subscribe(self, topic_structure: str):
        pass

    @abstractmethod
    def unsubscribe(self, topic_structure: str):
        pass
