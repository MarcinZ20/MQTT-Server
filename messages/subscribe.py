from dataclasses import dataclass
from io import BytesIO

from .header import Header
from .message import Message
from .structs import BYTE_ORDER, unpack_string


@dataclass
class RequestedTopic:
    topic_name: str
    qos: int


@dataclass
class SubscribeMessage(Message):
    """Subscribe message."""

    header: Header
    message_id: int
    requested_topics: list[RequestedTopic]

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'SubscribeMessage':
        """Creates the SUBSCRIBE message object from the given header and data."""

        message_id = int.from_bytes(data.read(2), BYTE_ORDER)

        topics = []
        data_length = len(data.getbuffer())
        while data.tell() < data_length:
            topic_name = unpack_string(data)
            qos = int.from_bytes(data.read(1), BYTE_ORDER)
            topics.append(RequestedTopic(topic_name, qos))

        return cls(header, message_id, topics)

    def pack(self) -> bytes:
        pass  # Not required for the server implementation
