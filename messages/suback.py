from dataclasses import dataclass
from io import BytesIO

from .header import Header
from .message import Message
from .structs import BYTE_ORDER, pack_remaining_length


@dataclass
class SubAckMessage(Message):
    """Subscribe Acknowledgment message."""

    header: Header
    message_id: int
    granted_qos: list[int]

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'SubAckMessage':
        pass  # Not required for the server implementation

    def pack(self) -> bytes:
        """Packs the message into a bytes object."""

        packed = self.header.pack()

        remaining_length = 2 + len(self.granted_qos)
        packed += pack_remaining_length(remaining_length)

        packed += self.message_id.to_bytes(2, BYTE_ORDER)

        for qos in self.granted_qos:
            packed += qos.to_bytes(1, BYTE_ORDER)

        return packed
