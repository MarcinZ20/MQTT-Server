from client_placeholder import ClientPlaceholder
from topic_manager import TopicManager

manager = TopicManager()

client1 = ClientPlaceholder("user1", "pass", manager)
client2 = ClientPlaceholder("user2", "pass", manager)
client3 = ClientPlaceholder("user3", "pass", manager)

client1.subscribe("test_topic")
client2.subscribe("test_topic")
client2.subscribe("other_topic")
client3.subscribe("other_topic")

client1.publish("test_topic", "Hello from client 1")
client1.publish("other_topic", "Hello from client 1, I'm not subscribed here")

client2.unsubscribe("test_topic")

client1.publish("test_topic", "Hello again from client 1, bye bye to client 2")
