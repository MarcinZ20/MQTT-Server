from client_placeholder import ClientPlaceholder
from topic_manager import TopicManager

manager = TopicManager()

client1 = ClientPlaceholder("user1", "pass", manager)
client2 = ClientPlaceholder("user2", "pass", manager)
client3 = ClientPlaceholder("user3", "pass", manager)
client4 = ClientPlaceholder("user4", "pass", manager)

client1.subscribe("test_topic")
client2.subscribe("test_topic")
client2.subscribe("other_topic")
client3.subscribe("other_topic")
client3.subscribe("test/+/efg")
client4.subscribe("test/#/abc")

client1.publish("test_topic", "Hello from client 1")
client1.publish("other_topic", "Hello from client 1, I'm not subscribed here")

client2.unsubscribe("test_topic")
try:
    client2.unsubscribe("test_topic")
except Warning as w:
    print(w)

client1.publish("test_topic", "Hello again from client 1, bye bye to client 2")
client1.publish("test/abc/efg", "Testing structured 1")
client1.publish("test/abc/xyz", "Testing structured 2")

client4.unsubscribe("test/#")
client1.publish("test/abc/xyz", "Testing structured 3")
