from src.connection.client import Client
from src.connection.message import *


class Topic:
    def __init__(self, topic_name: str):
        self.topic_name: str = topic_name
        self.subscribed_clients: set[Client] = set()
        self.messages: list[Message] = []
        self.retained_message: Message = Message()

    async def publish(self, message: PublishMessage):
        for client in self.subscribed_clients:
            await client.notify(message)

    def subscribe(self, client: Client):
        self.subscribed_clients.add(client)
        # TODO: verify retaining messages
        # client.notify(self.retained_message)

    def unsubscribe(self, client: Client):
        if client in self.subscribed_clients:
            self.subscribed_clients.remove(client)
        else:
            raise Warning(f"Warning: Client {client._address} not subscribed to topic {self.topic_name}")