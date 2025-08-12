import sys, pathlib
import numpy as np
import pygame

# Ensure src/ is on path
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / 'src'))

from client.gfx import postfx


def make_surface(color):
    surf = pygame.Surface((16, 16))
    surf.fill(color)
    return surf


def test_fx_toggle():
    pygame.init()
    base = make_surface((100, 100, 100))
    cfg_off = {}
    res_off = postfx.apply_chain(base, cfg_off)
    arr_base = pygame.surfarray.array3d(base)
    arr_off = pygame.surfarray.array3d(res_off)
    assert np.array_equal(arr_base, arr_off)

    cfg_on = {"fx_vignette": True, "fx_vignette_intensity": 1.0}
    res_on = postfx.apply_chain(base, cfg_on)
    arr_on = pygame.surfarray.array3d(res_on)
    assert not np.array_equal(arr_base, arr_on)
    pygame.quit()
