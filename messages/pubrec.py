from dataclasses import dataclass
from io import BytesIO

from .header import Header
from .message import Message
from .structs import BYTE_ORDER, pack_remaining_length


@dataclass
class PubRecMessage(Message):
    """Publish Received message."""

    header: Header
    message_id: int

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'PubRecMessage':
        """Creates the PUBREC message object from the given header and data."""

        message_id = int.from_bytes(data.read(2), BYTE_ORDER)

        return cls(header, message_id)

    def pack(self) -> bytes:
        """Packs the message into a bytes object."""

        packed = self.header.pack()

        remaining_length = 2
        packed += pack_remaining_length(remaining_length)

        packed += self.message_id.to_bytes(2, BYTE_ORDER)

        return packed
