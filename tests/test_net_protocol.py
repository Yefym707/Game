from net.protocol import (
    PROTOCOL_VERSION,
    MessageType,
    encode_message,
    decode_message,
)


def _round_trip(msg_type: MessageType) -> None:
    msg = {"t": msg_type.value}
    encoded = encode_message(msg)
    decoded = decode_message(encoded)
    assert decoded["t"] == msg_type.value
    assert decoded["v"] == PROTOCOL_VERSION


def test_round_trip_all_types() -> None:
    for mt in MessageType:
        _round_trip(mt)


def test_invalid_type() -> None:
    import pytest

    with pytest.raises(ValueError):
        decode_message("{}")


def test_version_int() -> None:
    assert isinstance(PROTOCOL_VERSION, int)
