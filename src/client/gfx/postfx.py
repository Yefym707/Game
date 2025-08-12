from __future__ import annotations

"""Simple post processing effects operating on :mod:`pygame` surfaces."""

from typing import Iterable
import pygame
import numpy as np

# ---------------------------------------------------------------------------
# individual effects

def vignette(surface: pygame.Surface, intensity: float = 0.5) -> pygame.Surface:
    """Darken edges using a radial gradient."""
    w, h = surface.get_size()
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2.0, h / 2.0
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    mask = 1.0 - dist / max_dist
    mask = np.clip(mask, 0, 1) ** 0.5
    mask = 1.0 - intensity * (1.0 - mask)
    arr *= mask[..., None]
    return pygame.surfarray.make_surface(arr.astype(np.uint8))


def desaturate(surface: pygame.Surface, amount: float = 1.0) -> pygame.Surface:
    """Linearly desaturate ``surface`` by ``amount`` in range [0, 1]."""
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    gray = arr.mean(axis=2, keepdims=True)
    arr = arr * (1.0 - amount) + gray * amount
    return pygame.surfarray.make_surface(arr.astype(np.uint8))


def color_curve(surface: pygame.Surface, matrix: Iterable[float]) -> pygame.Surface:
    """Apply a simple RGB color matrix.

    ``matrix`` should be an iterable with three scaling factors for R, G and B.
    """
    arr = pygame.surfarray.array3d(surface).astype(np.float32)
    r, g, b = matrix
    arr[..., 0] *= r
    arr[..., 1] *= g
    arr[..., 2] *= b
    arr = np.clip(arr, 0, 255)
    return pygame.surfarray.make_surface(arr.astype(np.uint8))


def _box_blur(arr: np.ndarray, radius: int = 1) -> np.ndarray:
    """Return blurred ``arr`` using a simple box blur."""
    if radius <= 0:
        return arr
    kernel = radius * 2 + 1
    pad = np.pad(arr, ((radius, radius), (radius, radius), (0, 0)), mode="edge")
    cumsum = pad.cumsum(0).cumsum(1)
    result = (
        cumsum[kernel:, kernel:] - cumsum[:-kernel, kernel:] - cumsum[kernel:, :-kernel] + cumsum[:-kernel, :-kernel]
    ) / (kernel * kernel)
    return result


def bloom(surface: pygame.Surface, intensity: float = 1.0) -> pygame.Surface:
    """Very small bloom using downsample + blur + add."""
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (max(1, w // 2), max(1, h // 2)))
    arr = pygame.surfarray.array3d(small).astype(np.float32)
    blurred = _box_blur(arr, 1)
    blurred_surf = pygame.surfarray.make_surface(np.clip(blurred, 0, 255).astype(np.uint8))
    blurred_up = pygame.transform.smoothscale(blurred_surf, (w, h))
    base = pygame.surfarray.array3d(surface).astype(np.float32)
    add = pygame.surfarray.array3d(blurred_up).astype(np.float32)
    base += add * intensity
    base = np.clip(base, 0, 255)
    return pygame.surfarray.make_surface(base.astype(np.uint8))


# ---------------------------------------------------------------------------
# pipeline helpers

_EFFECTS = [
    ("vignette", vignette),
    ("desaturate", desaturate),
    ("color", color_curve),
    ("bloom", bloom),
]


def apply_chain(surface: pygame.Surface, cfg) -> pygame.Surface:
    """Apply enabled effects in a fixed order returning a new surface."""
    result = surface
    for name, func in _EFFECTS:
        enabled_key = f"fx_{name}" if name != "color" else "fx_color"
        if not cfg.get(enabled_key):
            continue
        if name == "color":
            matrix = cfg.get("fx_color_curve", [1.0, 1.0, 1.0])
            result = func(result, matrix)
        else:
            intensity = cfg.get(f"fx_{name}_intensity", 1.0)
            result = func(result, intensity)
    return result


def count_enabled(cfg) -> int:
    """Return number of enabled effects based on ``cfg``."""
    count = 0
    for name, _ in _EFFECTS:
        key = f"fx_{name}" if name != "color" else "fx_color"
        if cfg.get(key):
            count += 1
    return count
