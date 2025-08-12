from __future__ import annotations

import asyncio


def _run_server(port_holder):
    clients = []

    async def handle(reader, writer):
        clients.append(writer)
        try:
            for _ in range(5):
                data = await reader.readline()
                if not data:
                    break
                writer.write(b'ack\n')
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def run():
        server = await asyncio.start_server(handle, '127.0.0.1', 0)
        port_holder.append(server.sockets[0].getsockname()[1])
        async with server:
            await server.serve_forever()

    return run()


def _run_client(port):
    async def run():
        reader, writer = await asyncio.open_connection('127.0.0.1', port)
        for _ in range(5):
            writer.write(b'hello\n')
            await writer.drain()
            await reader.readline()
        writer.close()
        await writer.wait_closed()
    return run()


def test_network_loop():
    port_holder: list[int] = []
    server_coro = _run_server(port_holder)
    async def runner():
        server_task = asyncio.create_task(server_coro)
        while not port_holder:
            await asyncio.sleep(0.01)
        port = port_holder[0]
        c1 = asyncio.create_task(_run_client(port))
        c2 = asyncio.create_task(_run_client(port))
        await asyncio.gather(c1, c2)
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task
    import contextlib
    asyncio.run(runner())
