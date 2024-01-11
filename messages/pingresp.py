from dataclasses import dataclass
from io import BytesIO

from .header import Header
from .message import Message
from .structs import pack_remaining_length


@dataclass
class PingRespMessage(Message):
    """Ping Response message."""

    header: Header

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'PingRespMessage':
        """Creates the PINGRESP message object from the given header and data."""

        return cls(header)

    def pack(self) -> bytes:
        """Packs the message into a bytes object."""

        packed = self.header.pack()
        remaining_length = 0
        packed += pack_remaining_length(remaining_length)

        return packed
