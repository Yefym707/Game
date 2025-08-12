import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from client.net_client import NetClient


def test_ping_rtt_smoothing() -> None:
    client = NetClient()
    client.record_rtt(0.1)
    client.record_rtt(0.2)
    assert client.rtt is not None
    assert abs(client.rtt - 0.15) < 1e-6

