from client_placeholder import ClientPlaceholder


class Topic:
    def __init__(self, topic_name: str):
        self.topic_name: str = topic_name
        self.subscribed_clients: set[ClientPlaceholder] = set()
        self.messages: list[str] = []  # TODO: Messages should have their own class it's not only string but also QoS etc.
        self.retained_message: str = ""

    def publish(self, message: str):
        for client in self.subscribed_clients:
            client.notify(message)

    def subscribe(self, client: ClientPlaceholder):
        self.subscribed_clients.add(client)
        # TODO: verify retaining messages
        # client.notify(self.retained_message)
        # TODO: send SUBACK

    def unsubscribe(self, client: ClientPlaceholder):
        self.subscribed_clients.remove(client)
        # TODO: send UNSUBACK
