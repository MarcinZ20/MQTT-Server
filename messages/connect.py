from dataclasses import dataclass
from io import BytesIO

from connection.constants import PROTOCOL_NAME, PROTOCOL_VERSION, MAXIMUM_CLIENT_ID_LENGTH
from exceptions.connection import MalformedPacketError, UnacceptableProtocolVersionError, IdentifierRejectedError
from .header import Header
from .message import Message
from .structs import BYTE_ORDER, CONNECT_FLAGS, unpack_string


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
