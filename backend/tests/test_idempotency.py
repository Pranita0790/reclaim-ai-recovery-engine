from app.models.decision import (
    DecisionStatus,
    RecoveryAction,
    RecoveryDecision,
)
from app.services.execution_service import ExecutionService


def create_decision() -> RecoveryDecision:
    """Create an approved recovery decision for execution tests."""

    return RecoveryDecision(
        case_id="IDEMPOTENCY-001",
        recommended_action=RecoveryAction.RETRY_PAYMENT,
        status=DecisionStatus.APPROVED,
        confidence=0.8,
        expected_recovery=4000.0,
        expected_value=3998.0,
        explanation="Test recovery decision.",
        evaluated_actions=[],
    )


# --------------------------------------------------
# TEST: SAME DECISION SHOULD NOT EXECUTE TWICE
# --------------------------------------------------

def test_same_decision_returns_same_execution() -> None:
    service = ExecutionService()

    decision = create_decision()

    first_result = service.execute(decision)
    second_result = service.execute(decision)

    assert (
        first_result.idempotency_key
        == second_result.idempotency_key
    )

    assert (
        first_result.execution_id
        == second_result.execution_id
    )

    assert (
        first_result.external_reference
        == second_result.external_reference
    )


# --------------------------------------------------
# TEST: DIFFERENT ACTIONS HAVE DIFFERENT EXECUTIONS
# --------------------------------------------------

def test_different_actions_generate_different_executions() -> None:
    service = ExecutionService()

    retry_decision = create_decision()

    contact_decision = retry_decision.model_copy(
        update={
            "recommended_action":
                RecoveryAction.CONTACT_CUSTOMER,
        }
    )

    retry_result = service.execute(retry_decision)
    contact_result = service.execute(contact_decision)

    assert (
        retry_result.idempotency_key
        != contact_result.idempotency_key
    )

    assert (
        retry_result.execution_id
        != contact_result.execution_id
    )


# --------------------------------------------------
# TEST: DIFFERENT CASES HAVE DIFFERENT EXECUTIONS
# --------------------------------------------------

def test_different_cases_generate_different_executions() -> None:
    service = ExecutionService()

    first_decision = create_decision()

    second_decision = first_decision.model_copy(
        update={
            "case_id": "IDEMPOTENCY-002",
        }
    )

    first_result = service.execute(first_decision)
    second_result = service.execute(second_decision)

    assert (
        first_result.idempotency_key
        != second_result.idempotency_key
    )

    assert (
        first_result.execution_id
        != second_result.execution_id
    )