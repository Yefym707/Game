"""Enemy and status effect logic used by the text based game.

This repository originally shipped without a functional implementation of
enemies which made running the interactive game impossible.  The module
below provides a small yet complete version of the original idea.  It is
intended to be simple so that it can be easily unit tested and serialised
when saving the game state.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import List, Optional, Tuple


@dataclass
class StatusEffect:
    """Represents a temporary effect that can be applied to the player."""

    effect_type: str
    duration: int

    def to_dict(self) -> dict:
        return {"effect_type": self.effect_type, "duration": self.duration}

    @staticmethod
    def from_dict(data: dict) -> "StatusEffect":
        return StatusEffect(data["effect_type"], int(data["duration"]))


class Enemy:
    """A very small enemy implementation.

    Each enemy knows its position, amount of health and the damage of its
    basic attack.  Enemies can move towards the player and attack him.  With
    a small chance the attack applies a ``poison`` status effect which is
    also returned to the caller so that the user interface can notify the
    player.
    """

    def __init__(self, pos: Tuple[int, int], health: int = 3, attack: int = 1):
        self.pos = pos
        self.health = health
        self.attack_damage = attack

    # ------------------------------------------------------------------
    def move_towards(self, target: Tuple[int, int], width: int, height: int, steps: int = 1) -> None:
        """Move the enemy towards ``target`` by ``steps`` tiles."""

        x, y = self.pos
        tx, ty = target
        for _ in range(steps):
            if x < tx:
                x += 1
            elif x > tx:
                x -= 1
            elif y < ty:
                y += 1
            elif y > ty:
                y -= 1
        self.pos = (max(0, min(width - 1, x)), max(0, min(height - 1, y)))

    def perform_attack(self, campaign) -> Optional[StatusEffect]:
        """Deal damage to the campaign's player and maybe return an effect."""

        campaign.player.damage(self.attack_damage)
        # To keep the game interesting there is a small chance to apply a
        # poison effect.  The random module is used directly so unit tests can
        # control the outcome by seeding it.
        if random.random() < 0.30:
            effect = StatusEffect("poison", duration=3)
            campaign.status_effects.append(effect)
            return effect
        return None

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {"pos": self.pos, "health": self.health, "attack": self.attack_damage}

    @staticmethod
    def from_dict(data: dict) -> "Enemy":
        return Enemy(tuple(data["pos"]), data.get("health", 3), data.get("attack", 1))


class EnemyManager:
    """Container handling a collection of :class:`Enemy` objects."""

    def __init__(self, enemies: List[Enemy]):
        self.enemies = enemies

    # factory -----------------------------------------------------------
    @staticmethod
    def spawn_on_map(
        width: int,
        height: int,
        count: int,
        player_pos: Tuple[int, int],
        health: int = 3,
        attack: int = 1,
    ) -> "EnemyManager":
        """Spawn ``count`` enemies on random positions of the map."""

        positions = {player_pos}
        enemies: List[Enemy] = []
        while len(enemies) < count:
            x, y = random.randint(0, width - 1), random.randint(0, height - 1)
            if (x, y) in positions:
                continue
            enemies.append(Enemy((x, y), health=health, attack=attack))
            positions.add((x, y))
        return EnemyManager(enemies)

    # update ------------------------------------------------------------
    def move_towards_player(self, player_pos: Tuple[int, int], width: int, height: int, campaign=None) -> None:
        """Move all enemies towards the player.

        Enemies become more aggressive at night and therefore move two tiles
        instead of one.  Only the ``time_of_day`` attribute of ``campaign`` is
        inspected which keeps the interface minimal.
        """

        steps = 2 if campaign and getattr(campaign, "time_of_day", "day") == "night" else 1
        target = player_pos
        if campaign and getattr(campaign, "decoy_pos", None) is not None:
            if any(e.effect_type == "decoy" for e in getattr(campaign, "status_effects", [])):
                target = campaign.decoy_pos
        for enemy in self.enemies:
            enemy.move_towards(target, width, height, steps)

    def get_enemy_at(self, pos: Tuple[int, int]) -> Optional[Enemy]:
        for enemy in self.enemies:
            if enemy.pos == pos:
                return enemy
        return None

    # serialisation -----------------------------------------------------
    def to_dict(self) -> dict:
        return {"enemies": [e.to_dict() for e in self.enemies]}

    @staticmethod
    def from_dict(data: dict) -> "EnemyManager":
        enemies = [Enemy.from_dict(d) for d in data.get("enemies", [])]
        return EnemyManager(enemies)

