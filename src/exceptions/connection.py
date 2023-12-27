class MQTTConnectionError(Exception):
    pass


class MalformedPacketError(MQTTConnectionError):
    pass


class UnacceptableProtocolVersionError(MalformedPacketError):
    pass


class IdentifierRejectedError(MQTTConnectionError):
    pass