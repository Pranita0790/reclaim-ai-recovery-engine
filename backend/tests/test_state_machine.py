from app.state_machine.recovery_state_machine import (
    InvalidStateTransitionError,
    RecoveryState,
    RecoveryStateMachine,
)


def print_test(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"TEST: {title}")
    print("=" * 60)


# ------------------------------------------------------------
# TEST 1: Valid recovery flow
# ------------------------------------------------------------

print_test("Valid Recovery Flow")

machine = RecoveryStateMachine()

print("Initial state:", machine.state.value)

machine.transition(RecoveryState.RECOVERABLE)
print("After case evaluation:", machine.state.value)

machine.transition(RecoveryState.DECISION_MADE)
print("After decision:", machine.state.value)

machine.transition(RecoveryState.EXECUTING)
print("During execution:", machine.state.value)

machine.transition(RecoveryState.RECOVERED)
print("Final state:", machine.state.value)

print("Is terminal:", machine.is_terminal())


# ------------------------------------------------------------
# TEST 2: Failed execution flow
# ------------------------------------------------------------

print_test("Failed Execution Flow")

machine = RecoveryStateMachine()

machine.transition(RecoveryState.RECOVERABLE)
machine.transition(RecoveryState.DECISION_MADE)
machine.transition(RecoveryState.EXECUTING)
machine.transition(RecoveryState.FAILED)

print("Final state:", machine.state.value)
print("Is terminal:", machine.is_terminal())


# ------------------------------------------------------------
# TEST 3: Expired recovery flow
# ------------------------------------------------------------

print_test("Expired Recovery Flow")

machine = RecoveryStateMachine()

machine.transition(RecoveryState.EXPIRED)

print("Final state:", machine.state.value)
print("Is terminal:", machine.is_terminal())


# ------------------------------------------------------------
# TEST 4: Invalid transition
# ------------------------------------------------------------

print_test("Invalid Transition")

machine = RecoveryStateMachine()

try:
    machine.transition(RecoveryState.RECOVERED)
except InvalidStateTransitionError as error:
    print("Expected error:", error)