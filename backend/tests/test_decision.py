from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)
from app.services.decision_engine import DecisionEngine


def run_test(test_name: str, case: RecoveryCase) -> None:
    print("\n" + "=" * 60)
    print(f"TEST: {test_name}")
    print("=" * 60)

    decision_engine = DecisionEngine()
    decision = decision_engine.decide(case)

    print(f"\nRecommended Action: {decision.recommended_action.value}")
    print(f"Decision Status: {decision.status.value}")
    print(f"Confidence: {decision.confidence}")
    print(f"Expected Value: {decision.expected_value}")
    print(f"Explanation: {decision.explanation}")

    print("\nAction Results:")

    for action in decision.evaluated_actions:
        print(
            f"- {action.action.value}: "
            f"Allowed={action.is_allowed}, "
            f"EV={action.expected_value}, "
            f"Reason={action.reason}"
        )


engine = DecisionEngine()


# ============================================================
# TEST 1: HAPPY PATH
# ============================================================

run_test(
    "Happy Path",
    RecoveryCase(
        case_id="CASE-001",
        customer_id="CUSTOMER-001",
        amount=5000.0,
        currency="INR",
        payment_status=PaymentStatus.FAILED,
        failure_reason=FailureReason.NETWORK_ERROR,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=1,
        is_customer_active=True,
        has_valid_payment_method=True,
    ),
)


# ============================================================
# TEST 2: MAX PAYMENT RETRIES REACHED
# ============================================================

run_test(
    "Maximum Payment Retries Reached",
    RecoveryCase(
        case_id="CASE-002",
        customer_id="CUSTOMER-002",
        amount=5000.0,
        payment_status=PaymentStatus.FAILED,
        failure_reason=FailureReason.CARD_DECLINED,
        failure_count=3,
        customer_attempt_count=0,
        days_since_failure=2,
        is_customer_active=True,
        has_valid_payment_method=True,
    ),
)


# ============================================================
# TEST 3: INVALID PAYMENT METHOD
# ============================================================

run_test(
    "Invalid Payment Method",
    RecoveryCase(
        case_id="CASE-003",
        customer_id="CUSTOMER-003",
        amount=5000.0,
        payment_status=PaymentStatus.FAILED,
        failure_reason=FailureReason.PAYMENT_METHOD_EXPIRED,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=1,
        is_customer_active=True,
        has_valid_payment_method=False,
    ),
)


# ============================================================
# TEST 4: MAX CUSTOMER ATTEMPTS REACHED
# ============================================================

run_test(
    "Maximum Customer Attempts Reached",
    RecoveryCase(
        case_id="CASE-004",
        customer_id="CUSTOMER-004",
        amount=5000.0,
        payment_status=PaymentStatus.FAILED,
        failure_reason=FailureReason.INSUFFICIENT_FUNDS,
        failure_count=1,
        customer_attempt_count=3,
        days_since_failure=2,
        is_customer_active=True,
        has_valid_payment_method=True,
    ),
)


# ============================================================
# TEST 5: AMOUNT BELOW ESCALATION THRESHOLD
# ============================================================

run_test(
    "Amount Below Escalation Threshold",
    RecoveryCase(
        case_id="CASE-005",
        customer_id="CUSTOMER-005",
        amount=500.0,
        payment_status=PaymentStatus.FAILED,
        failure_reason=FailureReason.NETWORK_ERROR,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=1,
        is_customer_active=True,
        has_valid_payment_method=True,
    ),
)


# ============================================================
# TEST 6: RECOVERY WINDOW EXPIRED
# ============================================================

run_test(
    "Recovery Window Expired",
    RecoveryCase(
        case_id="CASE-006",
        customer_id="CUSTOMER-006",
        amount=5000.0,
        payment_status=PaymentStatus.FAILED,
        failure_reason=FailureReason.NETWORK_ERROR,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=31,
        is_customer_active=True,
        has_valid_payment_method=True,
    ),
)