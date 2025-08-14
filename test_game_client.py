import asyncio
import contextlib
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from game_server import GameServer
from game_client import GameClient


def _run_server(port_holder):
    server = GameServer(port=0)

    async def run():
        srv = await asyncio.start_server(server.handle_client, server.host, 0)
        server._server = srv
        port_holder.append(srv.sockets[0].getsockname()[1])
        async with srv:
            await srv.serve_forever()

    return run()


def test_client_server_interaction():
    port_holder: list[int] = []
    server_coro = _run_server(port_holder)

    async def runner():
        server_task = asyncio.create_task(server_coro)
        while not port_holder:
            await asyncio.sleep(0.01)
        port = port_holder[0]
        client = GameClient(port=port)
        await client.connect()
        # wait for initial state from server
        await asyncio.sleep(0.05)
        await client.move(1, 0)
        await asyncio.sleep(0.1)
        assert client.board.grid[0][1] == "P"
        await client.close()
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task

    asyncio.run(runner())
