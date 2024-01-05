from topic import Topic
from client import Client
import re


class TopicManager:
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

    def publish_to_topic(self, topic_name: str, message: str):
        """
        Publishes message to given topic, creates on if such doesn't exist
        """
        topic_matched = False
        if TopicManager._is_valid_topic_name(topic_name):
            if topic_name in self._topics.keys():
                for client, topic_structure in self._wildcards_subscriptions:
                    self.subscribe_to_topic(topic_structure, client)
                self._topics[topic_name].publish(message)
                topic_matched = True

            if not topic_matched:
                self._create_topic(topic_name)
                for client, topic_structure in self._wildcards_subscriptions:
                    self.subscribe_to_topic(topic_structure, client)
                self.publish_to_topic(topic_name, message)

    def subscribe_to_topic(self, topic_structure: str, client: Client):
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
                self._topics[topic_name].subscribe(client)
                topic_matched = True

        if not topic_matched and TopicManager._is_valid_topic_name(topic_structure):
            self._create_topic(topic_structure)
            self.subscribe_to_topic(topic_structure, client)

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
            # TODO:
            #  1. Can unsubscribe message contain wildcards?
            #  2. What if I subscribe to "test/abc/#" but then unsubscribe from "test/abc/def"
            #  - would I receive message to every matching topic (eg. "test/abc/xyz") except "test/abc/def"?
            #  3. What if I subscribe to "test/+/xyz" and then unsubscribe from "test/#"?
            if wildcard_name == topic_structure:
                to_remove.add((client, wildcard_name))
                topic_matched = True
        for element in to_remove:
            self._wildcards_subscriptions.remove(element)

        if not topic_matched:
            raise Warning(f"Warning: No topic matching structure {topic_structure} exists")

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
