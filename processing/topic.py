from connection import Client
from messages import PublishMessage


class Topic:
    def __init__(self, topic_name: str):
        self.topic_name: str = topic_name
        self.subscribed_clients: set[Client] = set()
        # self.messages: list[Message] = []
        self.retained_message: PublishMessage | None = None

    async def publish(self, message: PublishMessage):
        if message.header.retain:
            self.retained_message = message if message.payload else None
        else:
            for client in self.subscribed_clients:
                await client.notify(message)

    async def subscribe(self, client: Client):
        self.subscribed_clients.add(client)

        if self.retained_message:
            await client.notify(self.retained_message)

    def unsubscribe(self, client: Client):
        if client in self.subscribed_clients:
            self.subscribed_clients.remove(client)
        else:
            raise Warning(f"Warning: Client {client._address} not subscribed to topic {self.topic_name}")
