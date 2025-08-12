"""Procedural sound effects with simple ADSR envelope.

This module generates short sound buffers on the fly using :mod:`numpy` and
converts them into ``pygame`` ``Sound`` objects.  No external audio files are
required which keeps the test environment lightweight.  A very small mixer is
used with three effect channels (``step``, ``hit`` and ``ui``) plus a master
volume.  Each channel can be controlled independently and an ADSR envelope is
applied for smooth fades.

The functions gracefully handle missing audio capabilities – if the mixer
cannot be initialised the play helpers simply do nothing which allows the rest
of the game to run in headless test environments.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np
import pygame

# mixer -----------------------------------------------------------------------

_SAMPLE_RATE = 44100
_INITIALISED = False
_AVAILABLE = False


def _ensure_init() -> None:
    """Initialise the pygame mixer if possible."""

    global _INITIALISED, _AVAILABLE
    if _INITIALISED:
        return
    _INITIALISED = True
    try:  # pragma: no cover - audio may be unavailable
        pygame.mixer.init(frequency=_SAMPLE_RATE, size=-16, channels=1)
        _AVAILABLE = True
    except Exception:
        _AVAILABLE = False


# volume handling --------------------------------------------------------------

_VOLUME: Dict[str, float] = {
    "master": 1.0,
    "step": 1.0,
    "hit": 1.0,
    "ui": 1.0,
}


def set_volume(value: float, channel: str = "master") -> None:
    """Set volume ``value`` for ``channel`` (0..1).

    ``channel`` defaults to ``master`` for backward compatibility with earlier
    versions that only exposed a single volume slider.
    """

    value = max(0.0, min(1.0, float(value)))
    _VOLUME[channel] = value


def init(cfg: Dict[str, float]) -> None:
    """Initialise volumes from configuration ``cfg``."""

    for ch in _VOLUME:
        set_volume(cfg.get(f"volume_{ch}", cfg.get("volume", 1.0)), ch)


# waveform generation ---------------------------------------------------------

def _adsr_envelope(n: int, attack: int, decay: int, sustain: float, release: int) -> np.ndarray:
    """Return an ADSR envelope for ``n`` samples."""

    a = int(_SAMPLE_RATE * attack / 1000.0)
    d = int(_SAMPLE_RATE * decay / 1000.0)
    r = int(_SAMPLE_RATE * release / 1000.0)
    s = max(0, n - a - d - r)
    env = np.concatenate(
        [
            np.linspace(0.0, 1.0, a, False),
            np.linspace(1.0, sustain, d, False),
            np.full(s, sustain),
            np.linspace(sustain, 0.0, r, False),
        ]
    )
    if len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return env


def generate_buffer(
    waveform: str,
    freq: float,
    ms: int,
    adsr: Tuple[int, int, float, int],
) -> np.ndarray:
    """Generate an int16 numpy buffer for a tone.

    Parameters
    ----------
    waveform:
        ``"sine"``, ``"square"`` or ``"triangle"``.
    freq:
        Frequency in Hz.
    ms:
        Duration in milliseconds.
    adsr:
        ``(attack_ms, decay_ms, sustain_level, release_ms)``
    """

    length = int(_SAMPLE_RATE * ms / 1000.0)
    t = np.linspace(0, ms / 1000.0, length, False)
    if waveform == "square":
        wave = np.sign(np.sin(2 * math.pi * freq * t))
    elif waveform == "triangle":
        wave = 2.0 / math.pi * np.arcsin(np.sin(2 * math.pi * freq * t))
    else:  # default to sine
        wave = np.sin(2 * math.pi * freq * t)
    env = _adsr_envelope(length, *adsr)
    wave *= env
    return (wave * 32767).astype(np.int16)


def _play(channel: str, waveform: str, freq: float, ms: int, adsr: Tuple[int, int, float, int]) -> None:
    """Generate and play a sound respecting channel volume."""

    _ensure_init()
    if not _AVAILABLE or not pygame.mixer.get_init():
        return
    try:
        snd = pygame.sndarray.make_sound(generate_buffer(waveform, freq, ms, adsr))
        snd.set_volume(_VOLUME.get(channel, 1.0) * _VOLUME["master"])
        snd.play()
    except Exception:  # pragma: no cover - mixer optional
        pass


# convenience play helpers ----------------------------------------------------

def play_step() -> None:
    """Play a short footstep sound."""

    _play("step", "square", 200, 80, (5, 20, 0.3, 60))


def play_hit() -> None:
    """Play a hit/attack sound."""

    _play("hit", "square", 400, 120, (0, 50, 0.2, 120))


def ui_click() -> None:
    """Play a tiny UI click respecting volume levels."""

    _play("ui", "sine", 880, 60, (5, 10, 0.5, 40))


__all__ = [
    "init",
    "set_volume",
    "generate_buffer",
    "play_step",
    "play_hit",
    "ui_click",
]

