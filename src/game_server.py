import asyncio
import json
from typing import Dict, Set

from game_board import GameBoard
from player import Player


class GameServer:
    """Simple asyncio based game server for multiplayer sessions.

    The server keeps an authoritative :class:`GameBoard` instance and a set of
    connected clients.  Clients communicate using JSON encoded messages where
    each message represents a player action.  After processing an action the
    updated game state is broadcast to all connected clients.

    The protocol is intentionally lightweight and primarily intended for unit
    tests and simple experiments.  Each message exchanged is a single line of
    UTF-8 encoded JSON.  Incoming messages must contain at least an ``action``
    field describing the desired operation, e.g. ``{"action": "move",
    "dx": 1, "dy": 0}``.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9999):
        self.host = host
        self.port = port
        self.board = GameBoard()
        # mapping from a client writer to the associated Player instance
        self.players: Dict[asyncio.StreamWriter, Player] = {}
        # active connections
        self.clients: Set[asyncio.StreamWriter] = set()
        self._server: asyncio.base_events.Server | None = None

    # ------------------------------------------------------------------
    # helper utilities
    def _serialise_state(self) -> dict:
        """Return a serialisable representation of the current game state."""

        return {
            "board": self.board.display_board(),
            "players": {id(w): p.to_dict() for w, p in self.players.items()},
        }

    async def _send_state(self, writer: asyncio.StreamWriter) -> None:
        data = json.dumps(self._serialise_state()).encode("utf-8") + b"\n"
        writer.write(data)
        await writer.drain()

    async def _broadcast_state(self) -> None:
        data = json.dumps(self._serialise_state()).encode("utf-8") + b"\n"
        for writer in list(self.clients):
            try:
                writer.write(data)
                await writer.drain()
            except ConnectionResetError:
                # drop dead connections silently
                self.clients.discard(writer)
                self.players.pop(writer, None)

    # ------------------------------------------------------------------
    # networking
    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle communication with a newly connected client."""

        # register client and spawn a fresh player
        self.clients.add(writer)
        player = Player()
        # find first free tile for the player
        spawn_x, spawn_y = 0, 0
        while not self.board.is_tile_free(spawn_x, spawn_y):
            spawn_x += 1
            if spawn_x >= self.board.width:
                spawn_x = 0
                spawn_y += 1
        self.board.place_entity(spawn_x, spawn_y, player.symbol)
        player.set_position(spawn_x, spawn_y)
        self.players[writer] = player

        await self._send_state(writer)

        try:
            while not reader.at_eof():
                line = await reader.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue  # ignore malformed messages
                await self._apply_action(msg, writer)
                await self._broadcast_state()
        finally:
            # cleanup on disconnect
            self.clients.discard(writer)
            p = self.players.pop(writer, None)
            if p is not None and self.board.within_bounds(p.x, p.y):
                self.board.remove_entity(p.x, p.y)
            writer.close()
            try:  # pragma: no cover - network cleanup is best effort
                await writer.wait_closed()
            except Exception:
                pass

    async def _apply_action(self, msg: dict, writer: asyncio.StreamWriter) -> None:
        """Apply a single action sent by ``writer`` to the game state."""

        player = self.players.get(writer)
        if player is None:
            return

        action = msg.get("action")
        if action == "move":
            dx = int(msg.get("dx", 0))
            dy = int(msg.get("dy", 0))
            player.start_turn(1)
            player.move(dx, dy, self.board)
        elif action == "attack":  # very lightweight: remove entity if present
            tx = int(msg.get("x", player.x))
            ty = int(msg.get("y", player.y))
            if self.board.within_bounds(tx, ty) and self.board.grid[ty][tx] == "Z":
                self.board.remove_entity(tx, ty)
        # ignore unknown actions

    async def start(self) -> None:
        """Start listening for incoming client connections."""

        self._server = await asyncio.start_server(self.handle_client, self.host, self.port)
        async with self._server:
            await self._server.serve_forever()


__all__ = ["GameServer"]
