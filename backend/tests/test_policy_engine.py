from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)
from app.models.decision import RecoveryAction
from app.services.policy_engine import PolicyEngine


def create_case(**overrides) -> RecoveryCase:
    """Create a valid recovery case for policy tests."""

    data = {
        "case_id": "POLICY-TEST-001",
        "customer_id": "CUSTOMER-001",
        "amount": 5000,
        "currency": "INR",
        "payment_status": PaymentStatus.RECOVERABLE,
        "failure_reason": FailureReason.NETWORK_ERROR,
        "failure_count": 1,
        "customer_attempt_count": 0,
        "days_since_failure": 1,
        "is_customer_active": True,
        "has_valid_payment_method": True,
        "metadata": {},
    }

    data.update(overrides)

    return RecoveryCase(**data)


def test_retry_payment_allowed() -> None:
    engine = PolicyEngine()
    case = create_case()

    allowed, reason = engine.evaluate(
        case,
        RecoveryAction.RETRY_PAYMENT,
    )

    assert allowed is True
    assert reason == "Payment retry is allowed."


def test_retry_payment_blocked_without_valid_payment_method() -> None:
    engine = PolicyEngine()
    case = create_case(
        has_valid_payment_method=False,
    )

    allowed, reason = engine.evaluate(
        case,
        RecoveryAction.RETRY_PAYMENT,
    )

    assert allowed is False
    assert reason == (
        "Customer does not have a valid payment method."
    )


def test_retry_payment_blocked_at_max_retries() -> None:
    engine = PolicyEngine()
    case = create_case(
        failure_count=3,
    )

    allowed, reason = engine.evaluate(
        case,
        RecoveryAction.RETRY_PAYMENT,
    )

    assert allowed is False
    assert "Maximum payment retries" in reason


def test_contact_customer_allowed() -> None:
    engine = PolicyEngine()
    case = create_case()

    allowed, reason = engine.evaluate(
        case,
        RecoveryAction.CONTACT_CUSTOMER,
    )

    assert allowed is True
    assert reason == "Customer contact is allowed."


def test_contact_customer_blocked_when_inactive() -> None:
    engine = PolicyEngine()
    case = create_case(
        is_customer_active=False,
    )

    allowed, reason = engine.evaluate(
        case,
        RecoveryAction.CONTACT_CUSTOMER,
    )

    assert allowed is False
    assert reason == "Customer is not active."


def test_contact_customer_blocked_at_max_attempts() -> None:
    engine = PolicyEngine()
    case = create_case(
        customer_attempt_count=3,
    )

    allowed, reason = engine.evaluate(
        case,
        RecoveryAction.CONTACT_CUSTOMER,
    )

    assert allowed is False
    assert "Maximum customer contact attempts" in reason


def test_escalation_allowed() -> None:
    engine = PolicyEngine()
    case = create_case(
        amount=5000,
    )

    allowed, reason = engine.evaluate(
        case,
        RecoveryAction.ESCALATE,
    )

    assert allowed is True
    assert reason == "Escalation is allowed."


def test_escalation_blocked_below_minimum_amount() -> None:
    engine = PolicyEngine()
    case = create_case(
        amount=500,
    )

    allowed, reason = engine.evaluate(
        case,
        RecoveryAction.ESCALATE,
    )

    assert allowed is False
    assert "minimum escalation threshold" in reason


def test_do_nothing_allowed() -> None:
    engine = PolicyEngine()
    case = create_case()

    allowed, reason = engine.evaluate(
        case,
        RecoveryAction.DO_NOTHING,
    )

    assert allowed is True
    assert reason == "No action is always allowed."


def test_all_actions_blocked_when_recovery_window_expired() -> None:
    engine = PolicyEngine()

    case = create_case(
        days_since_failure=31,
    )

    actions = [
        RecoveryAction.RETRY_PAYMENT,
        RecoveryAction.CONTACT_CUSTOMER,
        RecoveryAction.ESCALATE,
        RecoveryAction.DO_NOTHING,
    ]

    for action in actions:
        allowed, reason = engine.evaluate(
            case,
            action,
        )

        assert allowed is False
        assert reason == (
            "Automatic recovery window has expired."
        )