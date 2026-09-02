from __future__ import annotations

from enum import Enum


class RecoveryState(str, Enum):
    RECEIVED = "RECEIVED"
    RECOVERABLE = "RECOVERABLE"
    DECISION_MADE = "DECISION_MADE"
    EXECUTING = "EXECUTING"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class InvalidStateTransitionError(Exception):
    """Raised when an invalid recovery state transition is attempted."""


class RecoveryStateMachine:
    """Manage valid state transitions for a recovery case."""

    _ALLOWED_TRANSITIONS: dict[
        RecoveryState,
        set[RecoveryState],
    ] = {
        RecoveryState.RECEIVED: {
            RecoveryState.RECOVERABLE,
            RecoveryState.EXPIRED,
        },
        RecoveryState.RECOVERABLE: {
            RecoveryState.DECISION_MADE,
            RecoveryState.EXPIRED,
        },
        RecoveryState.DECISION_MADE: {
            RecoveryState.EXECUTING,
            RecoveryState.EXPIRED,
        },
        RecoveryState.EXECUTING: {
            RecoveryState.RECOVERED,
            RecoveryState.FAILED,
        },
        RecoveryState.RECOVERED: set(),
        RecoveryState.FAILED: set(),
        RecoveryState.EXPIRED: set(),
    }

    def __init__(
        self,
        initial_state: RecoveryState = RecoveryState.RECEIVED,
    ) -> None:
        self._state = initial_state

    @property
    def state(self) -> RecoveryState:
        """Return the current recovery state."""
        return self._state

    @property
    def current_state(self) -> RecoveryState:
        """Return the current recovery state."""
        return self._state

    def can_transition(
        self,
        new_state: RecoveryState,
    ) -> bool:
        """Return whether a transition to the new state is valid."""
        return new_state in self._ALLOWED_TRANSITIONS[
            self._state
        ]

    def transition(
        self,
        new_state: RecoveryState,
    ) -> RecoveryState:
        """Move to a new state if the transition is valid."""

        if not self.can_transition(new_state):
            raise InvalidStateTransitionError(
                (
                    f"Invalid transition from "
                    f"{self._state.value} to "
                    f"{new_state.value}."
                )
            )

        self._state = new_state

        return self._state

    def is_terminal(self) -> bool:
        """Return whether the current state is terminal."""

        return self._state in {
            RecoveryState.RECOVERED,
            RecoveryState.FAILED,
            RecoveryState.EXPIRED,
        }