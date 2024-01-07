import asyncio
import logging
from typing import TYPE_CHECKING, Callable

from exceptions.connection import (
    IdentifierRejectedError,
    UnacceptableProtocolVersionError,
    MalformedPacketError,
    GracePeriodExceededError
)
from .constants import ConnectReturnCode, MessageType
from .message import (
    Header,
    Message,
    ConnectMessage,
    ConnAckMessage,
    SubscribeMessage,
    SubAckMessage,
    UnsubscribeMessage,
    PublishMessage,
    PingReqMessage,
    DisconnectMessage,
    PubAckMessage,
    PingRespMessage,
    UnsubAckMessage,
    PubRecMessage,
    PubRelMessage,
    PubCompMessage
)
from .structs import pack_string

if TYPE_CHECKING:
    from .server import Server


log = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        server: 'Server',
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        auth_required: bool,
        address: str
    ):
        self.server = server
        self._reader = reader
        self._writer = writer
        self._auth_required = auth_required
        self._address = address
        self._closed = False

        self._keep_alive = None
        self._clean_session = None
        self._will_retain = None
        self._will_qos = None
        self._will_topic = None
        self._will_message = None

        self._actions: dict[MessageType, Callable] = {
            MessageType.SUBSCRIBE: self._on_subscribe,
            MessageType.UNSUBSCRIBE: self._on_unsubscribe,
            MessageType.PUBLISH: self._on_publish,
            MessageType.PINGREQ: self._on_ping,
            MessageType.DISCONNECT: self._on_disconnect,
            MessageType.PUBREL: self._on_pubrel,
            MessageType.PUBREC: self._on_pubrec
        }

    async def notify(self, message: PublishMessage):
        """Notifies the client."""

        await self._send_message(message)

    async def subscribe(self, topic_structure: str):
        await self.server.topic_manager.subscribe_to_topic(topic_structure, self)

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
            try:
                message = await Message.from_reader(self._reader, self._keep_alive)
            except (MalformedPacketError, GracePeriodExceededError):
                log.debug(f'Disconnecting {self._address} because of a malformed packet or exceeded grace period')

                if self._will_message is not None:
                    will_publish_message = PublishMessage(
                        Header(MessageType.PUBLISH, 0, self._will_qos, self._will_retain),
                        self._will_topic,
                        self.server.get_next_message_id(),
                        pack_string(self._will_message)
                    )

                    self.server.topic_manager.publish(will_publish_message)

                await self.close()
                return
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
                return False  # TODO: probably don't return here

            if self._auth_required:
                if not connect_message.user_name or not connect_message.password:
                    return_code = ConnectReturnCode.NOT_AUTHORIZED  # TODO: not sure if this is correct
                elif not self.server.auth_module.authenticate(connect_message.user_name, connect_message.password):
                    return_code = ConnectReturnCode.BAD_USER_NAME_OR_PASSWORD

            self._keep_alive = connect_message.keep_alive
            self._clean_session = connect_message.clean_session
            self._will_retain = connect_message.will_retain
            self._will_qos = connect_message.will_qos
            self._will_topic = connect_message.will_topic
            self._will_message = connect_message.will_message
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

        for topic in message.requested_topics:
            await self.server.topic_manager.subscribe_to_topic(topic.topic_name, self)

        granted_qos = [topic.qos for topic in message.requested_topics]

        log.debug(f'Sending SUBACK with granted QoS levels: {granted_qos}')

        suback_message = SubAckMessage(Header(MessageType.SUBACK), message.message_id, granted_qos)
        await self._send_message(suback_message)

    async def _on_unsubscribe(self, message: UnsubscribeMessage):
        """Handles an incoming UNSUBSCRIBE message."""

        log.debug(f'Received UNSUBSCRIBE from {self._address}')

        for topic in message.topics:
            self.server.topic_manager.unsubscribe_from_topic(topic, self)

        unsuback_message = UnsubAckMessage(Header(MessageType.UNSUBACK), message.message_id)

        await self._send_message(unsuback_message)

    async def _on_publish(self, message: PublishMessage):
        """Handles an incoming PUBLISH message."""

        log.debug(f'Received PUBLISH from {self._address}')

        await self.server.topic_manager.publish(message)

        qos = message.header.qos
        if not qos:
            return

        # PUBACK
        if qos == 1:
            puback_message = PubAckMessage(Header(MessageType.PUBACK, qos=1), message.message_id)

            await self._send_message(puback_message)
        # PUBREC
        else:
            pubrec_message = PubRecMessage(Header(MessageType.PUBREC, qos=2), message.message_id)

            await self._send_message(pubrec_message)

    async def _on_ping(self, message: PingReqMessage):
        """Handles an incoming PINGREQ message."""

        log.debug(f'Received PING from {self._address}')

        ping_message = PingRespMessage(Header(MessageType.PINGRESP))

        await self._send_message(ping_message)

    async def _on_pubrel(self, message: PubRelMessage):
        """Handles an incoming PUBREL message."""

        log.debug(f'Received PUBREL from {self._address}')

        pubcomp_message = PubCompMessage(Header(MessageType.PUBCOMP, qos=2), message.message_id)

        await self._send_message(pubcomp_message)

    async def _on_pubrec(self, message: PubRelMessage):
        """Handles an incoming PUBREC message."""

        log.debug(f'Received PUBREC from {self._address}')

        pubrel_message = PubRelMessage(Header(MessageType.PUBREL, qos=2), message.message_id)

        await self._send_message(pubrel_message)

    async def _on_disconnect(self, message: DisconnectMessage):
        """Handles an incoming DISCONNECT message."""

        log.debug(f'Received DISCONNECT from {self._address}')

        # TODO: retain?
        if self._clean_session:
            self.server.topic_manager.clear_session(self)

        await self.close()

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
