"""Entry point to run the master server."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import argparse
import asyncio

from master.run_master import run_master


def main() -> None:
    parser = argparse.ArgumentParser(description="Run master server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    ns = parser.parse_args()
    asyncio.run(run_master(ns.host, ns.port))


if __name__ == "__main__":  # pragma: no cover
    main()
