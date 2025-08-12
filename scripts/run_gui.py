"""Run the pygame GUI."""

import argparse

from client.app import main


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="run in demo mode")
    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover
    args = _parse_args()
    main(demo=args.demo)
