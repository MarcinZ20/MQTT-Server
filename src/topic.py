from client import Client


class Topic:
    def __init__(self, topic_name: str):
        self.topic_name: str = topic_name
        self.subscribed_clients: set[Client] = set()
        self.messages: list[str] = []  # TODO: Messages should have their own class it's not only string but also QoS etc.
        self.retained_message: str = ""

    def publish(self, message: str):
        for client in self.subscribed_clients:
            client.notify(message)

    def subscribe(self, client: Client):
        self.subscribed_clients.add(client)
        # TODO: verify retaining messages
        # client.notify(self.retained_message)
        # TODO: send SUBACK

    def unsubscribe(self, client: Client):
        if client in self.subscribed_clients:
            self.subscribed_clients.remove(client)
        else:
            raise Warning(f"Warning: Client {client.username} not subscribed to topic {self.topic_name}")
        # TODO: send UNSUBACK
