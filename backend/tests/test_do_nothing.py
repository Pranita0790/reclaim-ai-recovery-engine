from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)
from app.models.decision import RecoveryAction
from app.services.action_evaluator import ActionEvaluator


def create_case() -> RecoveryCase:
    """Create a standard recovery case."""

    return RecoveryCase(
        case_id="DO-NOTHING-001",
        customer_id="CUSTOMER-DO-NOTHING",
        amount=5000,
        currency="INR",
        payment_status=PaymentStatus.RECOVERABLE,
        failure_reason=FailureReason.NETWORK_ERROR,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=1,
        is_customer_active=True,
        has_valid_payment_method=True,
        metadata={},
    )


def test_do_nothing_is_allowed() -> None:
    evaluator = ActionEvaluator()

    case = create_case()

    result = evaluator.evaluate(
        case,
        RecoveryAction.DO_NOTHING,
    )

    assert result.action is RecoveryAction.DO_NOTHING
    assert result.is_allowed is True
    assert result.reason == "No action is always allowed."


def test_do_nothing_has_zero_success_probability() -> None:
    evaluator = ActionEvaluator()

    case = create_case()

    result = evaluator.evaluate(
        case,
        RecoveryAction.DO_NOTHING,
    )

    assert result.success_probability == 0.0


def test_do_nothing_has_zero_expected_recovery() -> None:
    evaluator = ActionEvaluator()

    case = create_case()

    result = evaluator.evaluate(
        case,
        RecoveryAction.DO_NOTHING,
    )

    assert result.expected_recovery == 0.0


def test_do_nothing_expected_value_reflects_action_cost() -> None:
    evaluator = ActionEvaluator()

    case = create_case()

    result = evaluator.evaluate(
        case,
        RecoveryAction.DO_NOTHING,
    )

    assert result.expected_value <= 0.0