"""Run the pygame GUI."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import argparse
import os

from client.app import main


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="run in demo mode")
    parser.add_argument("--safe", action="store_true", help="start in safe mode")
    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover
    args = _parse_args()
    safe = args.safe or bool(int(os.environ.get("GAME_SAFE_MODE", "0")))
    main(demo=args.demo, safe_mode=safe)
