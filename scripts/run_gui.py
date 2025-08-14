"""Entry point used during development.

This helper is aware of the ``sys._MEIPASS`` attribute injected by
PyInstaller so resources bundled with the executable are importable during
tests.  The pygame support prompt is hidden to keep the output clean.
"""

from pathlib import Path
import argparse
import os
import sys


def _add_src() -> None:
    """Insert the project's ``src`` directory into ``sys.path``.

    When packaged with PyInstaller the temporary extraction directory is
    available via ``sys._MEIPASS``.  During normal development we fall back to
    the repository root.
    """

    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    src = Path(base) / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--safe", action="store_true", help="start in safe mode")
    return parser.parse_args()


if __name__ == "__main__":  # pragma: no cover - manual invocation only
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    _add_src()
    try:
        from client.app import main
    except ModuleNotFoundError:  # pragma: no cover - exercised manually
        # The full graphical client isn't bundled with this kata repository.
        # Falling back to the console version ensures the entry point still
        # works for manual testing instead of crashing with an import error.
        from game import Game

        def main(*, safe_mode: bool = False) -> None:
            game = Game()
            game.run()

    args = _parse_args()
    safe = args.safe or bool(int(os.environ.get("GAME_SAFE_MODE", "0")))
    main(safe_mode=safe)
