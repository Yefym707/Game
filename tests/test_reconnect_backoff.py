import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from client.net_client import NetClient


def test_reconnect_backoff() -> None:
    client = NetClient(reconnect_backoff=[1, 2, 5, 10])
    assert [client.next_backoff() for _ in range(4)] == [1, 2, 5, 10]
    assert client.next_backoff() == 10
    client.reset_backoff()
    assert client.next_backoff() == 1

