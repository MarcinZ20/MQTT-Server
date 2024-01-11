from dataclasses import dataclass
from io import BytesIO

from .header import Header
from .message import Message


@dataclass
class PingReqMessage(Message):
    """Ping Request message."""

    header: Header

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'PingReqMessage':
        """Creates the PINGREQ message object from the given header and data."""

        return cls(header)

    def pack(self) -> bytes:
        pass  # Not required for the server implementation
