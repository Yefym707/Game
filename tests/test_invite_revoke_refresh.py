import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from server.invite import (
    create_invite,
    validate_invite,
    revoke_invite,
    refresh_invite,
)


def test_invite_revoke_refresh() -> None:
    secret = b"secret"
    invite = create_invite("h", 1, "room", secret, ttl=1)
    assert validate_invite(invite, secret)
    old = dict(invite)
    refreshed = refresh_invite(invite, secret, ttl=30)
    assert refreshed["code"] == invite["code"]
    assert refreshed["exp"] > old["exp"]
    assert validate_invite(refreshed, secret)
    assert not validate_invite(old, secret)
    revoke_invite(refreshed["code"])
    assert not validate_invite(refreshed, secret)

