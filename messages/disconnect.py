from dataclasses import dataclass
from io import BytesIO

from .header import Header
from .message import Message


@dataclass
class DisconnectMessage(Message):
    """Client is disconnecting message."""

    header: Header

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'DisconnectMessage':
        return cls(header)

    def pack(self) -> bytes:
        pass  # Not required for the server implementation
