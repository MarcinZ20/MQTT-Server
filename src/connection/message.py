import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO

from src.connection.constants import (
    PROTOCOL_NAME,
    PROTOCOL_VERSION,
    MAXIMUM_CLIENT_ID_LENGTH,
    MessageType,
    ConnectReturnCode
)
from src.connection.structs import (
    FIXED_HEADER,
    CONNECT_FLAGS,
    BYTE_ORDER,
    unpack_string, read_remaining_length, pack_remaining_length
)
from src.exceptions.connection import (
    MalformedPacketError,
    IdentifierRejectedError,
    UnacceptableProtocolVersionError
)


@dataclass
class RequestedTopic:
    topic_name: str
    qos: int


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

        remaining_length = await read_remaining_length(reader)

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

        protocol_version = int.from_bytes(data.read(1), BYTE_ORDER)
        if protocol_version != PROTOCOL_VERSION:
            raise UnacceptableProtocolVersionError('Invalid protocol version')

        connect_flags = data.read(1)
        user_name_flag, password_flag, will_retain, will_qos, will_flag, clean_session, _ = CONNECT_FLAGS.unpack(connect_flags)

        keep_alive = int.from_bytes(data.read(2), BYTE_ORDER)
        client_id = unpack_string(data)
        if not client_id:
            raise IdentifierRejectedError('Client Identifier too short')

        if len(client_id) > MAXIMUM_CLIENT_ID_LENGTH:
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
        packed += remaining_length.to_bytes(1, BYTE_ORDER)

        reserved_values = 0
        packed += reserved_values.to_bytes(1, BYTE_ORDER)

        packed += self.return_code.to_bytes(1, BYTE_ORDER)

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

    header: Header
    message_id: int
    requested_topics: list[RequestedTopic]

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'SubscribeMessage':
        """Creates the SUBSCRIBE message object from the given header and data."""

        message_id = int.from_bytes(data.read(2), BYTE_ORDER)

        topics = []
        data_length = len(data.getbuffer())
        while data.tell() < data_length:
            topic_name = unpack_string(data)
            qos = int.from_bytes(data.read(1), BYTE_ORDER)
            topics.append(RequestedTopic(topic_name, qos))

        return cls(header, message_id, topics)

    def pack(self) -> bytes:
        pass  # Not required for the server implementation


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


@dataclass
class PingRespMessage(Message):
    """Ping Response message."""
    pass


@dataclass
class DisconnectMessage(Message):
    """Client is disconnecting message."""
    header: Header

    @classmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'DisconnectMessage':
        return cls(header)

    def pack(self) -> bytes:
        pass # Not required for the server implementation


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
