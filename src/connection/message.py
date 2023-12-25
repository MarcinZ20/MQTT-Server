import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO

from src.connection.constants import PROTOCOL_NAME, PROTOCOL_VERSION, MessageType, ConnectReturnCode
from src.connection.structs import (
    FIXED_HEADER,
    CONNECT_FLAGS,
    unpack_string
)
from src.exceptions.connection import (
    MalformedPacketError,
    IdentifierRejectedError,
    UnacceptableProtocolVersionError
)


@dataclass
class Header:
    message_type: MessageType
    dup: int = 0
    qos: int = 0
    retain: int = 0

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Header':
        """Creates a header object from a bytes buffer."""

        return cls(*FIXED_HEADER.unpack(data))

    def pack(self) -> bytes:
        """Packs the header into a bytes buffer."""

        return FIXED_HEADER.pack(self.message_type, self.dup, self.qos, self.retain)


class Message(ABC):
    header: Header

    @classmethod
    async def from_reader(cls, reader: asyncio.StreamReader) -> 'Message':
        """Creates a message object from a reader stream."""

        buffer = await reader.readexactly(1)
        header = Header.from_bytes(buffer)

        remaining_length = 0
        multiplier = 1
        digit = 128

        while digit & 128:
            try:
                digit = (await reader.readexactly(1))[0]
            except asyncio.IncompleteReadError:
                raise MalformedPacketError('Header incomplete')

            remaining_length += (digit & 127) * multiplier
            multiplier *= 128

        # data - variable header and payload
        try:
            data = await reader.readexactly(remaining_length)
        except asyncio.IncompleteReadError:
            raise MalformedPacketError('Data incomplete')

        _class = MESSAGE_CLASSES.get(header.message_type)
        if _class is None:
            raise MalformedPacketError('Invalid message type')

        return _class.from_data(header, BytesIO(data))

    @classmethod
    @abstractmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'Message':
        """Creates a message object from the given header and data."""

    @abstractmethod
    def pack(self) -> bytes:
        """Packs the message into a bytes object."""


@dataclass
class ConnectMessage(Message):
    """Client request to connect to server message."""

    header: Header
    will_retain: bool
    will_qos: int
    clean_session: bool
    keep_alive: int
    client_id: str
    user_name: str | None
    password: str | None
    will_topic: str | None
    will_message: str | None

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'ConnectMessage':
        """Creates the CONNECT message object from the given header and data."""

        protocol_name = unpack_string(data)
        if protocol_name != PROTOCOL_NAME:
            raise MalformedPacketError('Invalid protocol name')

        protocol_version = int.from_bytes(data.read(1))
        if protocol_version != PROTOCOL_VERSION:
            raise UnacceptableProtocolVersionError('Invalid protocol version')

        connect_flags = data.read(1)
        user_name_flag, password_flag, will_retain, will_qos, will_flag, clean_session, _ = CONNECT_FLAGS.unpack(connect_flags)

        keep_alive = int.from_bytes(data.read(2))
        client_id = unpack_string(data)
        if not client_id:
            raise IdentifierRejectedError('Client Identifier too short')

        if len(client_id) > 23:
            raise IdentifierRejectedError('Client Identifier too long')

        will_topic = None
        will_message = None
        if will_flag:
            will_topic = unpack_string(data)
            will_message = unpack_string(data)

        user_name = None
        if user_name_flag:
            user_name = unpack_string(data)

        password = None
        if password_flag:
            password = unpack_string(data)

        return cls(
            header,
            will_retain,
            will_qos,
            clean_session,
            keep_alive,
            client_id,
            user_name,
            password,
            will_topic,
            will_message
        )

    def pack(self) -> bytes:
        pass  # Not required for the server implementation


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
        packed += remaining_length.to_bytes()

        reserves_values = 0
        packed += reserves_values.to_bytes()

        packed += self.return_code.to_bytes()

        return packed


# TODO: implement the other message classes
@dataclass
class PublishMessage(Message):
    """Publish message."""
    pass


@dataclass
class PubAckMessage(Message):
    """Publish Acknowledgement message."""
    pass


@dataclass
class PubRecMessage(Message):
    """Publish Received message."""
    pass


@dataclass
class PubRelMessage(Message):
    """Publish Released message."""
    pass


@dataclass
class PubCompMessage(Message):
    """Publish Complete message."""
    pass


@dataclass
class SubscribeMessage(Message):
    """Subscribe message."""
    pass


@dataclass
class SubAckMessage(Message):
    """Subscribe Acknowledgment message."""
    pass


@dataclass
class UnsubscribeMessage(Message):
    """Unsubscribe message."""
    pass


@dataclass
class UnsubAckMessage(Message):
    """Unsubscribe Acknowledgment message."""
    pass


@dataclass
class PingReqMessage(Message):
    """Ping Request message."""
    pass


@dataclass
class PingRespMessage(Message):
    """Ping Response message."""
    pass


@dataclass
class DisconnectMessage(Message):
    """Client is disconnecting message."""
    pass


MESSAGE_CLASSES: dict[MessageType, type[Message]] = {
    MessageType.CONNECT: ConnectMessage,
    MessageType.CONNACK: ConnAckMessage,
    MessageType.PUBLISH: PublishMessage,
    MessageType.PUBACK: PubAckMessage,
    MessageType.PUBREC: PubRecMessage,
    MessageType.PUBREL: PubRelMessage,
    MessageType.PUBCOMP: PubCompMessage,
    MessageType.SUBSCRIBE: SubscribeMessage,
    MessageType.SUBACK: SubAckMessage,
    MessageType.UNSUBSCRIBE: UnsubscribeMessage,
    MessageType.UNSUBACK: UnsubAckMessage,
    MessageType.PINGREQ: PingReqMessage,
    MessageType.PINGRESP: PingRespMessage,
    MessageType.DISCONNECT: DisconnectMessage
}
