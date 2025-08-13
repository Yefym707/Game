import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "src")])

from gamecore import board, rules, validate, i18n, events

i18n.set_language("en")


def test_turn_sequence() -> None:
    state = board.create_game(width=5, height=5, players=2)
    # move second player further away so we have space to walk
    state.players[1].x = 2
    state.players[1].y = 0
    rules.start_turn(state)

    ok, reason = rules.move(state, (1, 0))
    assert ok and reason is None
    assert (state.players[0].x, state.players[0].y) == (1, 0)

    ok, reason = rules.attack(state, state.players[1])
    assert ok and reason is None
    assert state.players[1].health == 7

    rules.end_turn(state)
    assert state.active == 1
    assert state.log == [events.MOVE, events.HIT, events.END_TURN]

    # invalid move: too far
    reason = validate.can_move(state, (4, 4))
    assert reason == i18n.gettext("out_of_range")

    # invalid attack: no AP
    state.current.ap = 0
    reason = validate.can_attack(state, state.players[0])
    assert reason == i18n.gettext("out_of_ap")
