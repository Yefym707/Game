"""Time-sliced resource loading helpers."""
from __future__ import annotations

import time
from typing import Callable, Generator, Iterable, List
import types


def _as_generator(task: Callable[[], object | Generator[None, None, None]]) -> Generator[None, None, None]:
    """Wrap ``task`` so it always returns a generator.

    ``task`` may either be a simple callable (executed once) or a generator
    yielding control between steps. The returned generator always runs the
    task to completion when iterated.
    """

    result = task()
    if isinstance(result, types.GeneratorType):
        return result

    def _wrapper() -> Generator[None, None, None]:
        task()  # type: ignore[misc]
        yield

    return _wrapper()


class AsyncLoader:
    """Process loader tasks without blocking the frame."""

    def __init__(self, tasks: Iterable[Callable[[], Generator[None, None, None] | object]], batch_ms: int) -> None:
        self.generators: List[Generator[None, None, None]] = [
            _as_generator(task) for task in tasks
        ]
        self.batch_ms = batch_ms
        self.index = 0

    def step(self) -> float:
        """Run tasks for at most ``batch_ms`` milliseconds.

        Returns the overall progress in percent.
        """

        start = time.perf_counter()
        while self.index < len(self.generators):
            gen = self.generators[self.index]
            try:
                next(gen)
            except StopIteration:
                self.index += 1
                continue
            if (time.perf_counter() - start) * 1000 >= self.batch_ms:
                break
        return self.progress

    @property
    def done(self) -> bool:
        """Return ``True`` when all tasks completed."""

        return self.index >= len(self.generators)

    @property
    def progress(self) -> float:
        """Return completion percentage from 0 to 100."""

        total = len(self.generators)
        if not total:
            return 100.0
        return (self.index / total) * 100.0

