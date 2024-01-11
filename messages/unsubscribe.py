from dataclasses import dataclass
from io import BytesIO

from .header import Header
from .message import Message
from .structs import BYTE_ORDER, unpack_string


@dataclass
class UnsubscribeMessage(Message):
    """Unsubscribe message."""

    header: Header
    message_id: int
    topics: list[str]

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'UnsubscribeMessage':
        message_id = int.from_bytes(data.read(2), BYTE_ORDER)
        topics = []
        data_length = len(data.getbuffer())
        while data.tell() < data_length:
            topic_name = unpack_string(data)
            topics.append(topic_name)

        return cls(header, message_id, topics)

    def pack(self) -> bytes:
        pass  # Not required for the server implementation
