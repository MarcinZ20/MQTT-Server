import re

from connection import Client
from messages import PublishMessage
from processing.topic import Topic


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TopicManager(metaclass=Singleton):
    """
    Class used to manage access to topics. Use it as a wrapper for Topic methods.
    """
    def __init__(self):
        self._topics: dict[str, Topic] = dict()
        self._wildcards_subscriptions: set[(Client, str)] = set()

    def _create_topic(self, topic_name: str):
        if topic_name in self._topics.keys():
            raise RuntimeWarning(f"Warning: Topic: {topic_name} already exists")  # Probably shouldn't get here?
        else:
            self._topics[topic_name] = Topic(topic_name)

    async def publish(self, message: PublishMessage):
        """
        Publishes message to given topic, creates on if such doesn't exist
        """
        topic_name = message.topic_name
        topic_matched = False
        if TopicManager._is_valid_topic_name(topic_name):
            if topic_name in self._topics.keys():
                for client, topic_structure in self._wildcards_subscriptions:
                    await self.subscribe_to_topic(topic_structure, client)
                await self._topics[topic_name].publish(message)
                topic_matched = True

            if not topic_matched:
                self._create_topic(topic_name)
                for client, topic_structure in self._wildcards_subscriptions:
                    await self.subscribe_to_topic(topic_structure, client)
                await self.publish(message)

    async def subscribe_to_topic(self, topic_structure: str, client: Client):
        """
        Subscribes client to every topic matching given topic_structure. \\
        If no topic is found, and topic_structure is a valid topic name - it creates and subscribes to a new topic
        :param topic_structure: string containing structure e.g. - "abc3/def" or "abc/#/xyz" or "a0" etc.
        :param client: subscribing client
        :return:
        """
        topic_matched = False
        for topic_name in self._topics.keys():
            if TopicManager._matches_name_with_structure(topic_name, topic_structure):
                await self._topics[topic_name].subscribe(client)
                topic_matched = True

        if not topic_matched and TopicManager._is_valid_topic_name(topic_structure):
            self._create_topic(topic_structure)
            await self.subscribe_to_topic(topic_structure, client)

        elif not TopicManager._is_valid_topic_name(topic_structure):
            if "#" in topic_structure:
                self._wildcards_subscriptions.add((client, topic_structure.split("#")[0]+"#"))
            else:
                self._wildcards_subscriptions.add((client, topic_structure))

    def unsubscribe_from_topic(self, topic_structure: str, client: Client):
        """
        Unsubscribes client from every topic matching topic_structure. Raises Warning when no topic matched
        """
        topic_matched = False
        for topic_name in self._topics.keys():
            if TopicManager._matches_name_with_structure(topic_name, topic_structure):
                self._topics[topic_name].unsubscribe(client)
                topic_matched = True

        to_remove: set[(Client, str)] = set()
        for client, wildcard_name in self._wildcards_subscriptions:
            if wildcard_name == topic_structure:
                to_remove.add((client, wildcard_name))
                topic_matched = True
        for element in to_remove:
            self._wildcards_subscriptions.remove(element)

        if not topic_matched:
            raise Warning(f"Warning: No topic matching structure {topic_structure} exists")

    def clear_session(self, client: Client):
        """Unsubscribe client from all topics. Used with clean_session flag"""
        for topic_name in self._topics.keys():
            try:
                self._topics[topic_name].unsubscribe(client)
            except Warning:
                pass
        self._wildcards_subscriptions = {(sub_client, topic) for sub_client, topic
                                         in self._wildcards_subscriptions if sub_client != client}
        return

    @staticmethod
    def _is_valid_topic_name(topic_name: str) -> bool:
        """
        Checks whether topic_name doesn't include wildcards, is not empty, \\
        contains at least on symbol after every '/' (if they're present).
        """
        topic_regex = re.compile(r'^[^#+/]+(/[^#+/]+)*$')
        return bool(topic_regex.match(topic_name)) and topic_name

    @staticmethod
    def _matches_name_with_structure(topic_name: str, topic_structure: str) -> bool:
        """
        Checks whether topic_name matches with given structure (string which may include wildcards - '#', '+')
        """
        pattern = topic_structure.replace('+', '[^/]*')
        if "#" in pattern:
            pattern = pattern.split("#")[0]+"#"
        pattern = pattern.replace('/#', '/.*')
        pattern = pattern.replace('#', '.*')
        pattern = '^' + pattern + '$'
        return bool(re.compile(pattern).match(topic_name))
