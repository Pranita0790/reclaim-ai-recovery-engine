from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)
from app.services.decision_engine import DecisionEngine


def test_ml_integrated_decision():

    case = RecoveryCase(
        case_id="ML-DECISION-001",
        customer_id="CUSTOMER-001",
        amount=5000,
        currency="INR",
        payment_status=PaymentStatus.RECOVERABLE,
        failure_reason=FailureReason.NETWORK_ERROR,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=1,
        is_customer_active=True,
        has_valid_payment_method=True,
    )

    decision_engine = DecisionEngine()

    decision = decision_engine.decide(case)

    print("\nML-INTEGRATED DECISION")

    print(
        "ML Recovery Probability:",
        decision.ml_recovery_probability,
    )

    print(
        "Recommended Action:",
        decision.recommended_action.value,
    )

    print(
        "Final Action Confidence:",
        decision.confidence,
    )

    print(
        "Expected Recovery:",
        decision.expected_recovery,
    )

    print(
        "Expected Value:",
        decision.expected_value,
    )

    print("\nACTION SCORES")

    for action in decision.evaluated_actions:

        print(
            action.action.value,
            "| Probability:",
            action.success_probability,
            "| Expected Value:",
            action.expected_value,
            "| Allowed:",
            action.is_allowed,
        )

    assert (
        0.0
        <= decision.ml_recovery_probability
        <= 1.0
    )

    assert (
        0.0
        <= decision.confidence
        <= 1.0
    )