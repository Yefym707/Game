from __future__ import annotations

"""Scenario settings for different game modes."""

from dataclasses import dataclass

from .rules import GameMode


@dataclass
class CampaignSettings:
    """Basic campaign parameters used when starting a game."""

    mode: GameMode = GameMode.SOLO
    players: int = 1
