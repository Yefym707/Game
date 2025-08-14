"""Utilities to handle turn order and rounds.

The original project only contained a very small stub for a turn manager
focussed on action points and phases.  For the tests and future gameplay we
require a component that can cycle through a list of participants (players or
enemies) and keep track of rounds.  Each participant receives a random number
of actions at the beginning of their turn.

The implementation below intentionally stays lightweight.  It stores a list of
participants and exposes :meth:`start_turn` and :meth:`end_turn` helpers.  The
former rolls a six sided die to determine how many actions the current
participant gets.  :meth:`end_turn` advances to the next participant and
increments the round counter once every participant has acted.  If a game state
is supplied an end-of-round event is drawn via :meth:`handle_end_of_round`.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple, Any, Sequence

import dice
from event_deck import draw_event, Event, GameState


class TurnManager:
    """Manage turn order for a list of participants.

    Parameters
    ----------
    participants:
        Iterable of objects representing the actors that take turns.  The
        objects are kept as-is which makes the manager agnostic of the actual
        player or enemy implementation.
    game_state:
        Optional :class:`event_deck.GameState` instance.  If provided a random
        event is drawn and resolved whenever a round finishes.
    event_deck:
        Optional sequence of :class:`event_deck.Event` objects to draw from.  If
        omitted the default event deck is used.
    """

    def __init__(
        self,
        participants: Iterable[Any],
        game_state: Optional[GameState] = None,
        event_deck: Optional[Sequence[Event]] = None,
    ) -> None:
        participants = list(participants)
        if not participants:
            raise ValueError("TurnManager requires at least one participant")
        self._participants: List[Any] = participants
        self._index: int = 0
        self.round: int = 1
        self.actions_left: int = 0
        self._game_state = game_state
        self._event_deck = event_deck

    # ------------------------------------------------------------------
    # helper properties
    @property
    def participants(self) -> List[Any]:
        """Return the list of managed participants."""

        return self._participants

    @property
    def current_player(self) -> Any:
        """Return the participant whose turn it is currently."""

        return self._participants[self._index]

    # ------------------------------------------------------------------
    # turn handling
    def start_turn(self, player: Optional[Any] = None) -> Tuple[Any, int]:
        """Start a turn for ``player`` and roll their action points.

        Parameters
        ----------
        player:
            Optional participant to start the turn for.  If omitted the current
            participant is used.  Passing an explicit participant also makes
            them the current one.

        Returns
        -------
        tuple
            ``(player, actions)`` where ``actions`` is the number of actions
            rolled for this turn.
        """

        if player is not None:
            try:
                self._index = self._participants.index(player)
            except ValueError:  # pragma: no cover - defensive programming
                raise ValueError("Unknown participant") from None

        player = self.current_player
        self.actions_left, _ = dice.roll("1d6")
        return player, self.actions_left

    def end_turn(self) -> Any:
        """Finish the current participant's turn and move to the next one.

        When the last participant ends their turn the round counter is
        increased and :meth:`handle_end_of_round` is invoked.

        Returns
        -------
        object
            The participant whose turn is next.
        """

        self._index += 1
        if self._index >= len(self._participants):
            self._index = 0
            self.round += 1
            self.handle_end_of_round()
        return self.current_player

    # ------------------------------------------------------------------
    def handle_end_of_round(self) -> None:
        """Trigger a random event when a game state is available."""

        if self._game_state is None:
            return None
        event = draw_event(self._game_state, self._event_deck)
        print(f"Event: {event.description}")
        return None


__all__ = ["TurnManager"]

