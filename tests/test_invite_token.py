import time
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from net.attestation import sign_invite, verify_invite


def _payload(exp: int) -> dict:
    return {
        "host": "localhost",
        "port": 1234,
        "room": "1",
        "exp": exp,
        "code": "ABCD-EFGH",
    }


def test_invite_signature_and_expiry() -> None:
    secret = b"secret"
    payload = _payload(int(time.time()) + 60)
    sig = sign_invite(payload, secret)
    assert verify_invite(payload, sig, secret)

    # expired
    expired = _payload(int(time.time()) - 1)
    sig2 = sign_invite(expired, secret)
    with pytest.raises(ValueError):
        verify_invite(expired, sig2, secret)

    # tamper
    bad = dict(payload)
    bad["room"] = "2"
    with pytest.raises(ValueError):
        verify_invite(bad, sig, secret)
