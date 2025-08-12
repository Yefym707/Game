from __future__ import annotations

import random
from typing import Any, Dict, Iterable, List, Sequence, TypeVar

T = TypeVar("T")


class RNG:
    """Wrapper around :class:`random.Random` with serialisable state."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random()
        self.seed(seed or 0)

    def seed(self, seed: int) -> None:
        """Initialise the generator with ``seed``."""
        self._seed = seed
        self._rng.seed(seed)

    # basic helpers -----------------------------------------------------
    def next(self) -> float:
        """Return the next floating point value in ``[0.0, 1.0)``."""
        return self._rng.random()

    def randrange(self, *args: int) -> int:
        return self._rng.randrange(*args)

    def choice(self, seq: Sequence[T]) -> T:
        return self._rng.choice(seq)

    def shuffle(self, seq: List[T]) -> None:
        self._rng.shuffle(seq)

    # serialisation -----------------------------------------------------
    def get_state(self) -> Dict[str, Any]:
        """Return a serialisable representation of the generator."""
        return {"seed": self._seed, "state": self._rng.getstate()}

    def set_state(self, data: Dict[str, Any]) -> None:
        """Restore generator state from :func:`get_state`."""
        def _to_tuple(obj: Any) -> Any:
            if isinstance(obj, list):
                return tuple(_to_tuple(x) for x in obj)
            return obj

        self._seed = int(data.get("seed", 0))
        self._rng.setstate(_to_tuple(data["state"]))
