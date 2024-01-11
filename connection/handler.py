from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any

from connection.structs import read_remaining_length
from exceptions.connection import GracePeriodExceededError, MalformedPacketError
from .message import Header, MESSAGE_CLASSES


class Handler(ABC):

    @abstractmethod
    def set_next(self, handler: Handler) -> Handler:
        pass

    @abstractmethod
    def handle(self, data: Any):
        pass


class AbstractHandler(Handler):

    _next_handler: AbstractHandler = None

    def set_next(self, handler: AbstractHandler) -> 'AbstractHandler':
        self._next_handler = handler
        return self._next_handler

    async def handle(self, *args, **kwargs):
        result = await self.process(*args, **kwargs)

        if self._next_handler:
            await self._next_handler.handle(*result)

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
    async def process(self, reader: asyncio.StreamReader):
        remaining_length = await read_remaining_length(reader)
        return reader, remaining_length, Header


class DataHandler(AbstractHandler):
    async def process(self, reader: asyncio.StreamReader, remaining_length: int):
        try:
            data = await reader.readexactly(remaining_length)
        except asyncio.IncompleteReadError:
            raise MalformedPacketError('Data incomplete')

        return reader, Header, data


class MessageHandler(AbstractHandler):
    async def process(self, header: Header, data: bytes):
        _class = MESSAGE_CLASSES.get(header.message_type)
        if _class is None:
            raise MalformedPacketError('Invalid message type')

        return _class.from_data(header, BytesIO(data))
