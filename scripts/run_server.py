"""Entry point to run the websocket server."""
from __future__ import annotations

import argparse
import asyncio

from server.run_server import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run game server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    ns = parser.parse_args()
    asyncio.run(run(ns.host, ns.port))


if __name__ == "__main__":  # pragma: no cover
    main()
