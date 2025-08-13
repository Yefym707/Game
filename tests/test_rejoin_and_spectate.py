import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from server.game_room import GameRoom
from server.lobby import Lobby


def test_rejoin_and_spectator() -> None:
    lobby = Lobby("1", "test", max_players=2, allow_drop_in=True, allow_spectators=True)
    room = GameRoom("1")
    token = room.add_player("alice")
    lobby.rejoin_tokens["alice"] = token
    lobby.remove_player("alice")
    room.drop_player("alice")
    assert lobby.rejoin("alice", token)
    snap = room.rejoin_player("alice", token)
    assert "alice" in room.state["players"]
    assert snap == room.snapshot()
    assert lobby.add_spectator("bob")
    room.add_spectator("bob")
    assert "bob" in room.spectators
