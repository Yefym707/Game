import time
import pytest

from server.game_room import GameRoom
from server.banlist import BanList
from server.security import SessionGuard


def test_invalid_action_rejected():
    room = GameRoom("lobby")
    room.apply_action({"seq": 1, "end_turn": True})
    with pytest.raises(ValueError):
        room.apply_action({"seq": 2, "hack": True})


def test_ban_ip(tmp_path):
    bl = BanList(tmp_path / "ban.json")
    bl.ban_ip("1.2.3.4", seconds=1)
    assert bl.is_banned("1.2.3.4")
    time.sleep(1.2)
    assert not bl.is_banned("1.2.3.4")


def test_rate_limit():
    guard = SessionGuard(actions_per_sec=2)
    guard.check()
    guard.check()
    with pytest.raises(ValueError):
        guard.check()
