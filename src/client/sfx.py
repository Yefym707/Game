from __future__ import annotations

"""Tiny sound effect helpers.

The real game plays short procedural tones generated in memory.  The
implementation here keeps things extremely small so it works even in the
restricted test environment where audio output may not be available.  If the
pygame mixer cannot be initialised the functions simply do nothing.
"""

from typing import Dict
import math

import numpy as np
import pygame

# ---------------------------------------------------------------------------

_INITIALISED = False


def _ensure_init() -> None:
    global _INITIALISED
    if _INITIALISED:
        return
    try:  # pragma: no cover - audio may be unavailable
        pygame.mixer.init()
    except Exception:
        return
    _INITIALISED = True


def tone(freq: int = 440, ms: int = 120) -> pygame.mixer.Sound | None:
    """Return a pygame ``Sound`` object for a sine wave tone."""

    _ensure_init()
    if not pygame.mixer.get_init():
        return None
    sample_rate = 44100
    t = np.linspace(0, ms / 1000.0, int(sample_rate * ms / 1000.0), False)
    wave = (np.sin(freq * 2 * math.pi * t) * 32767).astype(np.int16)
    try:
        return pygame.sndarray.make_sound(wave)
    except Exception:  # pragma: no cover - mixer may not support sndarray
        return None


class SFX:
    """Container holding a couple of pre-generated effects."""

    def __init__(self) -> None:
        self.sounds: Dict[str, pygame.mixer.Sound | None] = {
            "step": tone(660, 80),
            "hit": tone(440, 120),
            "pickup": tone(880, 120),
        }

    def play(self, name: str) -> None:
        snd = self.sounds.get(name)
        if snd:
            try:  # pragma: no cover - audio playback
                snd.play()
            except Exception:
                pass


_VOLUME = 1.0


def set_volume(v: float) -> None:
    """Set global playback volume."""

    global _VOLUME
    _VOLUME = max(0.0, min(1.0, v))
    try:  # pragma: no cover - mixer optional
        pygame.mixer.music.set_volume(_VOLUME)
    except Exception:
        pass


def ui_click() -> None:
    """Play a short UI click tone respecting global volume."""

    snd = tone(880, 50)
    if snd:
        try:  # pragma: no cover - audio playback optional
            snd.set_volume(_VOLUME)
            snd.play()
        except Exception:
            pass
