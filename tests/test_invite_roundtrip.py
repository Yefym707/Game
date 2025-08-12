import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from server.invite import create_invite
from net.serialization import parse_invite_url
from net.attestation import verify_invite


def test_invite_roundtrip() -> None:
    secret = b"secret"
    invite = create_invite("host", 9999, "room1", secret, ttl=60)
    parsed = parse_invite_url(invite["url"])
    assert parsed["host"] == "host"
    assert parsed["port"] == 9999
    assert parsed["room"] == "room1"
    assert parsed["code"] == invite["code"]
    assert verify_invite(
        {k: parsed[k] for k in ("host", "port", "room", "exp", "code")},
        parsed["sig"],
        secret,
    )
