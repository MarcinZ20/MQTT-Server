from dataclasses import dataclass
from io import BytesIO

from .header import Header
from .message import Message
from .structs import BYTE_ORDER, pack_remaining_length, pack_string, unpack_string


@dataclass
class PublishMessage(Message):
    """Publish message."""

    header: Header
    topic_name: str
    message_id: int | None
    payload: bytes

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'PublishMessage':
        """Creates the PUBLISH message object from the given header and data."""

        topic_name = unpack_string(data)

        message_id = None
        if header.qos > 0:
            message_id = int.from_bytes(data.read(2), BYTE_ORDER)

        payload = data.read()

        return cls(header, topic_name, message_id, payload)

    def pack(self) -> bytes:
        """Packs the message into a bytes object."""

        packed = self.header.pack()

        # every string is 2 + its length
        remaining_length = 2 + len(self.topic_name) + len(self.payload)
        if self.header.qos > 0:
            remaining_length += 2  # message id has length 2

        packed += pack_remaining_length(remaining_length)

        packed += pack_string(self.topic_name)
        if self.header.qos > 0:
            packed += self.message_id.to_bytes(2, BYTE_ORDER)

        packed += self.payload

        return packed
