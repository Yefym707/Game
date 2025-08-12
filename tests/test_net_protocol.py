from net.protocol import (
    PROTOCOL_VERSION,
    MessageType,
    encode_message,
    decode_message,
)


def test_round_trip() -> None:
    msg = {"t": MessageType.PING.value}
    encoded = encode_message(msg)
    decoded = decode_message(encoded)
    assert decoded["t"] == MessageType.PING.value
    assert decoded["v"] == PROTOCOL_VERSION


def test_invalid_type() -> None:
    import pytest

    with pytest.raises(ValueError):
        decode_message("{}")


def test_version_int() -> None:
    assert isinstance(PROTOCOL_VERSION, int)
