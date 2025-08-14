from types import SimpleNamespace

from src.scenario import Scenario
from src.player import Player


def test_item_completion():
    scenario = Scenario(
        name="Scenario 1 – The Antidote",
        description="Find the antidote",
        win_condition={"item": "antidote"},
    )
    player = Player()
    state = SimpleNamespace(players=[player], turn=1)
    assert not scenario.is_completed(state)
    player.pick_up("antidote")
    assert scenario.is_completed(state)


def test_location_completion():
    scenario = Scenario(
        name="Escape",
        description="Reach exit at (2, 3)",
        win_condition={"location": (2, 3)},
    )
    player = Player(0, 0)
    state = SimpleNamespace(players=[player], turn=1)
    assert not scenario.is_completed(state)
    player.set_position(2, 3)
    assert scenario.is_completed(state)


def test_survive_turns_completion():
    scenario = Scenario(
        name="Hold out",
        description="Survive for three turns",
        win_condition={"survive_turns": 3},
    )
    state = SimpleNamespace(players=[], turn=2)
    assert not scenario.is_completed(state)
    state.turn = 3
    assert scenario.is_completed(state)
