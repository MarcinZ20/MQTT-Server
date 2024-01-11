import asyncio
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, TYPE_CHECKING

from connection.constants import MessageType
from exceptions.connection import GracePeriodExceededError, MalformedPacketError
from .header import Header
from .structs import read_remaining_length

if TYPE_CHECKING:
    from .message import Message


class Handler(ABC):
    @abstractmethod
    def set_next(self, handler: 'Handler') -> 'Handler':
        pass

    @abstractmethod
    def handle(self, data: Any):
        pass


class AbstractHandler(Handler):
    _next_handler: 'AbstractHandler' = None

    def set_next(self, handler: 'AbstractHandler') -> 'AbstractHandler':
        self._next_handler = handler
        return self._next_handler

    async def handle(self, *args, **kwargs):
        result = await self.process(*args, **kwargs)

        if self._next_handler:
            return await self._next_handler.handle(*result)

        return result

    async def process(self, *args, **kwargs):
        # To be overridden by concrete handlers
        raise NotImplementedError("Subclasses must implement the process method")


class HeaderHandler(AbstractHandler):
    async def process(self, reader: asyncio.StreamReader, keep_alive: int = None):
        grace_period = int(keep_alive * 1.5) if keep_alive else None

        try:
            buffer = await asyncio.wait_for(reader.readexactly(1), grace_period)
        except asyncio.TimeoutError:
            raise GracePeriodExceededError('No message from client within 1.5 x keep alive')

        return reader, Header.from_bytes(buffer)


class RemainingLengthHandler(AbstractHandler):
    async def process(self, reader: asyncio.StreamReader, header: Header):
        remaining_length = await read_remaining_length(reader)

        return reader, header, remaining_length


class DataHandler(AbstractHandler):
    async def process(self, reader: asyncio.StreamReader, header: Header, remaining_length: int):
        try:
            data = await reader.readexactly(remaining_length)
        except asyncio.IncompleteReadError:
            raise MalformedPacketError('Data incomplete')

        return header, data


class MessageHandler(AbstractHandler):
    async def process(self, header: Header, data: bytes):
        _class = get_message_class(header.message_type)
        if _class is None:
            raise MalformedPacketError('Invalid message type')

        return _class.from_data(header, BytesIO(data))


def get_message_class(message_type: MessageType) -> type['Message']:
    """Gets the message class based on the message type."""

    from .connack import ConnAckMessage
    from .connect import ConnectMessage
    from .disconnect import DisconnectMessage
    from .pingreq import PingReqMessage
    from .pingresp import PingRespMessage
    from .puback import PubAckMessage
    from .pubcomp import PubCompMessage
    from .publish import PublishMessage
    from .pubrec import PubRecMessage
    from .pubrel import PubRelMessage
    from .suback import SubAckMessage
    from .subscribe import SubscribeMessage
    from .unsuback import UnsubAckMessage
    from .unsubscribe import UnsubscribeMessage

    messages_classes: dict[MessageType, type['Message']] = {
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

    return messages_classes.get(message_type)
