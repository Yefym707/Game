import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from server.lobby import Lobby
from server.game_room import GameRoom


def test_lobby_ready_start() -> None:
    lobby = Lobby("1", "test", max_players=2)
    lobby.add_player("alice")
    lobby.add_player("bob")
    lobby.set_ready("alice", True)
    lobby.set_ready("bob", True)
    room = GameRoom("1")
    assert lobby.all_ready()
    assert room.start(lobby)
    lobby.set_ready("bob", False)
    assert not lobby.all_ready()
    assert not room.can_start(lobby)

