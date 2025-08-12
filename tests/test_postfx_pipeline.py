from __future__ import annotations

import sys
import pathlib
import pygame

# ensure src is on path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from client.gfx import postfx


def test_pipeline_order(monkeypatch):
    surf = pygame.Surface((8, 8))
    order = []

    def stub(name):
        def _fx(s, *args, **kwargs):
            order.append(name)
            return s
        return _fx

    monkeypatch.setattr(postfx, "vignette", stub("vignette"))
    monkeypatch.setattr(postfx, "desaturate", stub("desaturate"))
    monkeypatch.setattr(postfx, "color_curve", stub("color"))
    monkeypatch.setattr(postfx, "bloom", stub("bloom"))
    monkeypatch.setattr(
        postfx,
        "_EFFECTS",
        [("vignette", postfx.vignette), ("desaturate", postfx.desaturate), ("color", postfx.color_curve), ("bloom", postfx.bloom)],
    )

    cfg = {
        "fx_vignette": True,
        "fx_desaturate": True,
        "fx_color": True,
        "fx_color_curve": [1.0, 1.0, 1.0],
        "fx_bloom": True,
    }
    postfx.apply_chain(surf, cfg)
    assert order == ["vignette", "desaturate", "color", "bloom"]


def test_toggle_no_crash():
    surf = pygame.Surface((4, 4))
    cfg = {
        "fx_vignette": False,
        "fx_desaturate": False,
        "fx_color": False,
        "fx_bloom": False,
    }
    postfx.apply_chain(surf, cfg)
    cfg.update({"fx_vignette": True, "fx_desaturate": True, "fx_color": True, "fx_bloom": True})
    cfg["fx_color_curve"] = [1, 1, 1]
    cfg["fx_vignette_intensity"] = cfg["fx_desaturate_intensity"] = cfg["fx_bloom_intensity"] = 0.5
    postfx.apply_chain(surf, cfg)

