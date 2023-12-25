from io import BytesIO

import bitstruct

from src.exceptions.connection import MalformedPacketError

FIXED_HEADER = bitstruct.compile('u4u1u2u1')
CONNECT_FLAGS = bitstruct.compile('u1u1u1u2u1u1u1')


def unpack_string(data: BytesIO) -> str:
    """Unpacks a string from the BytesIO object."""

    length = int.from_bytes(data.read(2))

    try:
        return data.read(length).decode()
    except UnicodeDecodeError:
        raise MalformedPacketError('Invalid UTF-8 encoded string.')


def pack_string(data: str) -> bytes:
    """Packs a string into a bytes object."""

    packed = len(data).to_bytes(2)
    return packed + data.encode()
