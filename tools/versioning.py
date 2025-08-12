import subprocess
from typing import Final


def get_version() -> str:
    """Return version from ``git describe --tags`` or a dev fallback.

    When the repository has no tags or git is unavailable the
    function returns ``0.0.0+dev``.
    """
    try:
        output = subprocess.check_output(
            ["git", "describe", "--tags"], stderr=subprocess.DEVNULL
        )
    except Exception:  # pragma: no cover - fallback logic
        return "0.0.0+dev"
    return output.decode().strip()


__all__: Final = ["get_version"]
__version__: str = get_version()
