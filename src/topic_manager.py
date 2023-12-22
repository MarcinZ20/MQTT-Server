from topic import Topic
from client_placeholder import ClientPlaceholder
import re


class TopicManager:
    """
    Class used to manage access to topics. Use it as a wrapper for Topic methods.
    """
    def __init__(self):
        self.topics: dict[str, Topic] = dict()

    def _create_topic(self, topic_name: str):
        if topic_name in self.topics.keys():
            raise RuntimeWarning(f"Topic: {topic_name} already exists")  # Probably shouldn't get here?
        else:
            self.topics[topic_name] = Topic(topic_name)

    def publish_to_topic(self, topic_structure: str, message: str):
        """
        Publishes message to every Topic where topic_name matches given topic_structure. \\
        If topic_structure doesn't contain any wildcards and topic doesn't exist, \\
        then it creates new topic and publishes to it
        :param topic_structure: given structure including wildcards "#" and "+"
        :param message: message to publish
        :return:
        """
        topic_matched = False
        for topic_name in self.topics.keys():
            if TopicManager._matches_name_with_structure(topic_name, topic_structure):
                self.topics[topic_name].publish(message)
                topic_matched = True

        if not topic_matched and TopicManager._is_valid_topic_name(topic_structure):
            self._create_topic(topic_structure)
            self.publish_to_topic(topic_structure, message)

    def subscribe_to_topic(self, topic_structure: str, client: ClientPlaceholder):
        """
        Subscribes client to every topic matching given topic_structure. \\
        If no topic is found, and topic_structure is a valid topic name - it creates and subscribes to a new topic
        :param topic_structure: string containing structure e.g. - "abc3/def" or "abc/#/xyz" or "a0" etc.
        :param client: subscribing client
        :return:
        """
        topic_matched = False
        for topic_name in self.topics.keys():
            if TopicManager._matches_name_with_structure(topic_name, topic_structure):
                self.topics[topic_name].subscribe(client)
                topic_matched = True

        if not topic_matched and TopicManager._is_valid_topic_name(topic_structure):
            self._create_topic(topic_structure)
            self.subscribe_to_topic(topic_structure, client)

    def unsubscribe_from_topic(self, topic_structure: str, client: ClientPlaceholder):
        """
        Unsubscribes client from every topic matching topic_structure. Raises warning when no topic matched
        :param topic_structure: used to match to topic name
        :param client: client trying to unsubscribe
        :raises Warning when trying to unsubscribe and no topic is matched
        :return:
        """
        topic_matched = False
        for topic_name in self.topics.keys():
            if TopicManager._matches_name_with_structure(topic_name, topic_structure):
                self.topics[topic_name].unsubscribe(client)
                topic_matched = True

        if not topic_matched:
            raise Warning(f"No topic matching structure {topic_structure} exists")

    @staticmethod
    def _is_valid_topic_name(topic_name: str) -> bool:
        """
        Checks whether topic_name doesn't include wildcards, is not empty, \\
        contains at least on symbol after every '/' (if they're present).
        :param topic_name: topic name to check
        :return: True if it is a valid topic_name
        """
        topic_regex = re.compile(r'^[^#+/]+(/[^#+/]+)*$')
        return bool(topic_regex.match(topic_name)) and topic_name

    @staticmethod
    def _matches_name_with_structure(topic_name: str, topic_structure: str) -> bool:
        # TODO: write this better, include wildcards etc
        return topic_name == topic_structure
