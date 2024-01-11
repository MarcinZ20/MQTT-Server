from dataclasses import dataclass
from io import BytesIO

from .header import Header
from .message import Message
from .structs import BYTE_ORDER, pack_remaining_length


@dataclass
class UnsubAckMessage(Message):
    """Unsubscribe Acknowledgment message."""

    header: Header
    message_id: int

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'UnsubAckMessage':
        pass  # Not required for the server implementation

    def pack(self) -> bytes:
        """Packs the message into a bytes object."""

        packed = self.header.pack()
        remaining_length = 2
        packed += pack_remaining_length(remaining_length)
        packed += self.message_id.to_bytes(2, BYTE_ORDER)

        return packed
