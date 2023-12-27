import asyncio
import logging
from typing import TYPE_CHECKING

from src.connection.constants import ConnectReturnCode, MessageType
from src.connection.message import Message, ConnectMessage, ConnAckMessage, Header
from src.exceptions.connection import IdentifierRejectedError, UnacceptableProtocolVersionError

if TYPE_CHECKING:
    from src.connection.server import Server


log = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        server: 'Server',
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        auth_required: bool
    ):
        self.server = server
        self._reader = reader
        self._writer = writer
        self._auth_required = auth_required

    async def serve(self):
        """Serves the client connection."""

        address = self._writer.get_extra_info('peername')
        log.info(f'New client connection from {address[0]}:{address[1]}')

        return_code = ConnectReturnCode.ACCEPTED
        try:
            connect_message = await Message.from_reader(self._reader)
            if not isinstance(connect_message, ConnectMessage):
                return  # TODO: probably don't return here

            if self._auth_required:
                if not connect_message.user_name or not connect_message.password:
                    return_code = ConnectReturnCode.NOT_AUTHORIZED  # TODO: not sure if this is correct
                else:
                    # TODO: change this to use the auth module
                    authorized = False
                    for user_name, password in self.server.users:
                        if user_name == connect_message.user_name and password == connect_message.password:
                            authorized = True
                            break

                    if not authorized:
                        return_code = ConnectReturnCode.BAD_USER_NAME_OR_PASSWORD

            # TODO: do something with the remaining attributes of the CONNECT message
        except IdentifierRejectedError:
            return_code = ConnectReturnCode.IDENTIFIER_REJECTED
        except UnacceptableProtocolVersionError:
            return_code = ConnectReturnCode.UNACCEPTABLE_PROTOCOL_VERSION

        log.debug(f'Sending CONNACK with status {return_code.name}')

        connack_message = ConnAckMessage(Header(MessageType.CONNACK), return_code)
        await self._write_message(connack_message)

        if return_code != ConnectReturnCode.ACCEPTED:
            return

        while True:
            message = await Message.from_reader(self._reader)
            print(message.header)

            # TODO: act accordingly depending on the message type

    async def _write_message(self, message: Message):
        """Writes a message to the client."""

        self._writer.write(message.pack())
        await self._writer.drain()

    async def close(self):
        """Closes the client connection."""

        self._writer.close()
        await self._writer.wait_closed()
