from dataclasses import dataclass
from io import BytesIO

from connection.constants import ConnectReturnCode
from .header import Header
from .message import Message
from .structs import BYTE_ORDER


@dataclass
class ConnAckMessage(Message):
    """Connect Acknowledgement message."""

    header: Header
    return_code: ConnectReturnCode

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'Message':
        pass  # Not required for the server implementation

    def pack(self) -> bytes:
        """Packs the message into a bytes object."""

        packed = self.header.pack()

        remaining_length = 2
        packed += remaining_length.to_bytes(1, BYTE_ORDER)

        reserved_values = 0
        packed += reserved_values.to_bytes(1, BYTE_ORDER)

        packed += self.return_code.to_bytes(1, BYTE_ORDER)

        return packed
