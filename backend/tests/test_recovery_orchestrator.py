from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)
from app.services.recovery_orchestrator import (
    RecoveryOrchestrator,
)


def print_test(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"TEST: {title}")
    print("=" * 60)


def print_result(result) -> None:
    print("Case ID:", result.case.case_id)
    print(
        "Recommended Action:",
        result.decision.recommended_action.value,
    )
    print(
        "Decision Status:",
        result.decision.status.value,
    )
    print(
        "Execution Status:",
        result.execution.status.value,
    )
    print(
        "Final State:",
        result.final_state.value,
    )

    print("\nAudit Events:")

    for event in result.audit_events:
        print(
            f"- {event.event_type.value}: "
            f"{event.message}"
        )


orchestrator = RecoveryOrchestrator()


# ------------------------------------------------------------
# TEST 1: Successful Recovery
# ------------------------------------------------------------

print_test("Successful Recovery")

successful_case = RecoveryCase(
    case_id="CASE-ORCH-001",
    customer_id="CUSTOMER-001",
    amount=5000.0,
    payment_status=PaymentStatus.RECOVERABLE,
    failure_reason=FailureReason.NETWORK_ERROR,
    failure_count=1,
    customer_attempt_count=0,
    days_since_failure=1,
    is_customer_active=True,
    has_valid_payment_method=True,
)

result = orchestrator.process(successful_case)

print_result(result)


# ------------------------------------------------------------
# TEST 2: Expired Recovery Case
# ------------------------------------------------------------

print_test("Expired Recovery Case")

expired_case = RecoveryCase(
    case_id="CASE-ORCH-002",
    customer_id="CUSTOMER-002",
    amount=5000.0,
    payment_status=PaymentStatus.EXPIRED,
    failure_reason=FailureReason.INSUFFICIENT_FUNDS,
    failure_count=3,
    customer_attempt_count=3,
    days_since_failure=31,
    is_customer_active=False,
    has_valid_payment_method=False,
)

result = orchestrator.process(expired_case)

print_result(result)


# ------------------------------------------------------------
# TEST 3: Retry Not Allowed
# ------------------------------------------------------------

print_test("Retry Not Allowed")

restricted_case = RecoveryCase(
    case_id="CASE-ORCH-003",
    customer_id="CUSTOMER-003",
    amount=5000.0,
    payment_status=PaymentStatus.RECOVERABLE,
    failure_reason=FailureReason.CARD_DECLINED,
    failure_count=3,
    customer_attempt_count=0,
    days_since_failure=2,
    is_customer_active=True,
    has_valid_payment_method=False,
)

result = orchestrator.process(restricted_case)

print_result(result)