import json

from gamecore import board as gboard
from gamecore import events, scenario, rules


def test_events_trigger_and_effect(tmp_path):
    evs = events.load_events()
    assert len(evs) >= 10
    state = gboard.create_game()
    balance = {"events": {"chance": 1.0}}
    ev = events.maybe_trigger(state, balance)
    assert ev is not None
    events.apply_effect(state, ev.effects[0])
    assert "medkit" in state.current.inventory or state.current.health != 10


def test_scenarios_apply():
    scens = scenario.load_scenarios()
    assert {"short", "medium", "long"}.issubset(set(scens))
    state = gboard.create_game()
    scenario.apply_scenario(state, scens["short"])
    assert "knife" in state.players[0].inventory
    assert state.board.width == 10
    assert rules.CURRENT_DIFFICULTY == rules.Difficulty.EASY
