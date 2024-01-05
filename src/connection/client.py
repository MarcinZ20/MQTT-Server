import asyncio
import logging
from typing import TYPE_CHECKING, Callable

from src.connection.constants import ConnectReturnCode, MessageType
from src.connection.message import (
    Header,
    Message,
    ConnectMessage,
    ConnAckMessage,
    SubscribeMessage,
    SubAckMessage,
    UnsubscribeMessage,
    PublishMessage,
    PingReqMessage,
    DisconnectMessage, PubAckMessage, PingRespMessage
)
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

        ip, port = self._writer.get_extra_info('peername')
        self._address = f'{ip}:{port}'

        self._closed = False

        self._actions: dict[MessageType, Callable] = {
            MessageType.SUBSCRIBE: self._on_subscribe,
            MessageType.UNSUBSCRIBE: self._on_unsubscribe,
            MessageType.PUBLISH: self._on_publish,
            MessageType.PINGREQ: self._on_ping,
            MessageType.DISCONNECT: self._on_disconnect
        }

    async def notify(self, message: PublishMessage):
        """Notifies the client."""

        await self._send_message(message)

    def subscribe(self, topic_structure: str):
        self.server.topic_manager.subscribe_to_topic(topic_structure, self)

    def unsubscribe(self, topic_structure: str):
        self.server.topic_manager.unsubscribe_from_topic(topic_structure, self)

    async def serve(self):
        """Serves the client connection."""

        log.info(f'New client connection from {self._address}')

        connected = await self._connect()
        if not connected:
            await self.close()
            return

        while True:
            message = await Message.from_reader(self._reader)
            if message is None:
                log.warning('Received a message but it has not been implemented!')
                continue

            action = self._actions.get(message.header.message_type)
            if action is None:
                log.warning(f'Action not implemented for message of type {message.header.message_type.name}!')
                continue

            await action(message)

            if self._closed:
                return

    async def _connect(self) -> bool:
        """
        Awaits a CONNECT message from the client and sends a CONNACK.
        Returns whether the connection was successful.
        """

        return_code = ConnectReturnCode.ACCEPTED
        try:
            connect_message = await Message.from_reader(self._reader)
            if not isinstance(connect_message, ConnectMessage):
                return False # TODO: probably don't return here

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
        await self._send_message(connack_message)

        return return_code == ConnectReturnCode.ACCEPTED

    async def _on_subscribe(self, message: SubscribeMessage):
        """Handles an incoming SUBSCRIBE message."""

        # TODO: subscribe to the topics
        for topic in message.requested_topics:
            self.server.topic_manager.subscribe_to_topic(topic.topic_name, self)

        granted_qos = [topic.qos for topic in message.requested_topics]

        log.debug(f'Sending SUBACK with granted QoS levels: {granted_qos}')

        suback_message = SubAckMessage(Header(MessageType.SUBACK), message.message_id, granted_qos)
        await self._send_message(suback_message)

    async def _on_unsubscribe(self, message: UnsubscribeMessage):
        """Handles an incoming UNSUBSCRIBE message."""

        # TODO: implement

    async def _on_publish(self, message: PublishMessage):
        """Handles an incoming PUBLISH message."""

        log.debug(f'Received PUBLISH from {self._address}')

        self.server.topic_manager.publish_to_topic(message)

        qos = message.header.qos
        if not qos:
            return

        # PUBACK
        if qos == 1:
            puback_message = PubAckMessage(Header(MessageType.PUBACK), message.message_id)

            await self._send_message(puback_message)
        # PUBREC
        else:
            pass  # TODO: implement PUBREC response

    async def _on_ping(self, message: PingReqMessage):
        """Handles an incoming PINGREQ message."""

        log.debug(f'Received PING from {self._address}')

        ping_message = PingRespMessage(Header(MessageType.PINGRESP))

        await self._send_message(ping_message)

    async def _on_disconnect(self, message: DisconnectMessage):
        """Handles an incoming DISCONNECT message."""

        # TODO: implement

    async def _send_message(self, message: Message):
        """Sends a message to the client."""

        self._writer.write(message.pack())
        await self._writer.drain()

    def is_closed(self) -> bool:
        """Checks if the client connection has been closed."""

        return self._closed

    async def close(self):
        """Closes the client connection."""

        self._closed = True
        self._writer.close()
        await self._writer.wait_closed()
