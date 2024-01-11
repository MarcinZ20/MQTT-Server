import asyncio
from abc import ABC, abstractmethod
from io import BytesIO

from messages.header import Header
from .handler import HeaderHandler, RemainingLengthHandler, DataHandler, MessageHandler


class Message(ABC):
    header: Header

    @classmethod
    async def from_reader(cls, reader: asyncio.StreamReader, keep_alive: int = None) -> 'Message':
        """Creates a message object from a reader stream."""

        # grace_period = int(keep_alive * 1.5) if keep_alive else None
        #
        # try:
        #     buffer = await asyncio.wait_for(reader.readexactly(1), grace_period)
        # except asyncio.TimeoutError:
        #     raise GracePeriodExceededError('No message from client within 1.5 x keep alive')
        #
        # header = Header.from_bytes(buffer)
        #
        # remaining_length = await read_remaining_length(reader)
        #
        # # data - variable header and payload
        # try:
        #     data = await reader.readexactly(remaining_length)
        # except asyncio.IncompleteReadError:
        #     raise MalformedPacketError('Data incomplete')
        #
        # _class = MESSAGE_CLASSES.get(header.message_type)
        # if _class is None:
        #     raise MalformedPacketError('Invalid message type')
        #
        # return _class.from_data(header, BytesIO(data))

        header_handler = HeaderHandler()
        length_handler = RemainingLengthHandler()
        data_handler = DataHandler()
        message_handler = MessageHandler()

        header_handler.set_next(length_handler).set_next(data_handler).set_next(message_handler)
        return await header_handler.handle(reader, keep_alive)

    @classmethod
    @abstractmethod
    def from_data(cls, header: Header, data: BytesIO) -> 'Message':
        """Creates a message object from the given header and data."""

    @abstractmethod
    def pack(self) -> bytes:
        """Packs the message into a bytes object."""
