from __future__ import annotations

from dataclasses import dataclass
from typing import List

from . import entities, rules


@dataclass
class Deck:
    cards: List[entities.Item]

    def __post_init__(self) -> None:
        rules.RNG.shuffle(self.cards)
        self.discard: List[entities.Item] = []

    def draw(self) -> entities.Item:
        if not self.cards:
            self.cards, self.discard = self.discard, []
            rules.RNG.shuffle(self.cards)
        card = self.cards.pop()
        self.discard.append(card)
        return card


def default_deck() -> Deck:
    items = [
        entities.Item("food", "R"),
        entities.Item("medkit", "H"),
        entities.Item("weapon", "G"),
        entities.Item("antidote", "A"),
    ]
    return Deck(items)
