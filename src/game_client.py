import asyncio
import json
import contextlib
from typing import Dict, Any

from game_board import GameBoard


class GameClient:
    """Async client used by players to talk to :class:`GameServer`.

    The client is intentionally thin – it connects to the server, sends
    high level player commands and keeps a local representation of the
    game state based on updates received from the server.  Communication
    happens via newline separated JSON messages.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9999,
        *,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 0.5,
    ) -> None:
        self.host = host
        self.port = port
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay

        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.listen_task: asyncio.Task | None = None
        self.connected: bool = False

        # local representation of the game state
        self.board = GameBoard()
        self.players: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    async def connect(self) -> None:
        """Connect to the server and start listening for updates."""

        for attempt in range(self.reconnect_attempts + 1):
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    self.host, self.port
                )
                self.connected = True
                self.listen_task = asyncio.create_task(self._listen())
                return
            except (OSError, ConnectionRefusedError):
                self.connected = False
                if attempt >= self.reconnect_attempts:
                    raise
                await asyncio.sleep(self.reconnect_delay)

    async def _listen(self) -> None:
        assert self.reader is not None
        try:
            while True:
                line = await self.reader.readline()
                if not line:
                    break
                try:
                    state = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                self._apply_state(state)
        finally:
            self.connected = False
            # best effort reconnect
            if self.reconnect_attempts > 0:
                for _ in range(self.reconnect_attempts):
                    try:
                        await asyncio.sleep(self.reconnect_delay)
                        await self.connect()
                        return
                    except Exception:
                        continue

    # ------------------------------------------------------------------
    def _apply_state(self, state: Dict[str, Any]) -> None:
        """Update local game state from ``state`` received from server."""

        board = state.get("board")
        if isinstance(board, str):
            rows = board.splitlines()
            self.board.height = len(rows)
            self.board.width = len(rows[0]) if rows else 0
            self.board.grid = [
                [None if ch == "." else ch for ch in row] for row in rows
            ]

        players = state.get("players")
        if isinstance(players, dict):
            self.players = players

    # ------------------------------------------------------------------
    async def send_action(self, action: Dict[str, Any]) -> None:
        """Send ``action`` dictionary to the server."""

        if not self.connected or self.writer is None:
            raise ConnectionError("Not connected to server")
        data = json.dumps(action).encode("utf-8") + b"\n"
        self.writer.write(data)
        await self.writer.drain()

    async def move(self, dx: int, dy: int) -> None:
        await self.send_action({"action": "move", "dx": dx, "dy": dy})

    async def attack(self, x: int, y: int) -> None:
        await self.send_action({"action": "attack", "x": x, "y": y})

    async def command(self, text: str) -> None:
        """Parse a textual ``text`` command and send the appropriate action."""

        parts = text.strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        if cmd == "move" and len(parts) == 2:
            direction = parts[1].lower()
            mapping = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
            if direction in mapping:
                dx, dy = mapping[direction]
                await self.move(dx, dy)
        elif cmd == "attack" and len(parts) == 3:
            try:
                x, y = int(parts[1]), int(parts[2])
            except ValueError:
                return
            await self.attack(x, y)

    # ------------------------------------------------------------------
    async def close(self) -> None:
        """Close the connection to the server."""

        if self.listen_task:
            self.listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.listen_task
        if self.writer is not None:
            self.writer.close()
            with contextlib.suppress(Exception):
                await self.writer.wait_closed()
        self.connected = False


__all__ = ["GameClient"]
