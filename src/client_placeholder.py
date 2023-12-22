from topic_manager import TopicManager
from client import Client


class ClientPlaceholder(Client):
    def __init__(self, username: str, password: str, manager: TopicManager):
        super().__init__(username, password)
        self.manager = manager

    def notify(self, message: str):
        print(f'Client: {self.username} notified with message: {message}')

    def publish(self, topic_structure: str, message: str):
        self.manager.publish_to_topic(topic_structure, message)

    def subscribe(self, topic_structure: str):
        self.manager.subscribe_to_topic(topic_structure, self)

    def unsubscribe(self, topic_structure: str):
        self.manager.unsubscribe_from_topic(topic_structure, self)
