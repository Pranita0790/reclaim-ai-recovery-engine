from app.models.decision import (
    DecisionStatus,
    RecoveryAction,
    RecoveryDecision,
)
from app.services.execution_service import ExecutionService


def print_test(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"TEST: {title}")
    print("=" * 60)


def print_result(result) -> None:
    print("Case ID:", result.case_id)
    print("Action:", result.action.value)
    print("Status:", result.status.value)
    print("Message:", result.message)
    print("Idempotency Key:", result.idempotency_key)
    print("External Reference:", result.external_reference)


execution_service = ExecutionService()


# ------------------------------------------------------------
# TEST 1: Approved payment retry
# ------------------------------------------------------------

print_test("Approved Payment Retry")

approved_decision = RecoveryDecision(
    case_id="CASE-001",
    recommended_action=RecoveryAction.RETRY_PAYMENT,
    status=DecisionStatus.APPROVED,
    confidence=0.79,
    expected_recovery=3950.0,
    expected_value=3948.0,
    explanation="Payment retry is expected to recover the highest value.",
    evaluated_actions=[],
)

result = execution_service.execute(approved_decision)

print_result(result)


# ------------------------------------------------------------
# TEST 2: Rejected decision
# ------------------------------------------------------------

print_test("Rejected Decision")

rejected_decision = RecoveryDecision(
    case_id="CASE-002",
    recommended_action=RecoveryAction.DO_NOTHING,
    status=DecisionStatus.REJECTED,
    confidence=0.0,
    expected_recovery=0.0,
    expected_value=0.0,
    explanation="No positive recovery value.",
    evaluated_actions=[],
)

result = execution_service.execute(rejected_decision)

print_result(result)


# ------------------------------------------------------------
# TEST 3: Blocked decision
# ------------------------------------------------------------

print_test("Blocked By Policy")

blocked_decision = RecoveryDecision(
    case_id="CASE-003",
    recommended_action=RecoveryAction.DO_NOTHING,
    status=DecisionStatus.BLOCKED_BY_POLICY,
    confidence=0.0,
    expected_recovery=0.0,
    expected_value=0.0,
    explanation="Recovery window expired.",
    evaluated_actions=[],
)

result = execution_service.execute(blocked_decision)

print_result(result)


# ------------------------------------------------------------
# TEST 4: Approved contact customer
# ------------------------------------------------------------

print_test("Approved Customer Contact")

contact_decision = RecoveryDecision(
    case_id="CASE-004",
    recommended_action=RecoveryAction.CONTACT_CUSTOMER,
    status=DecisionStatus.APPROVED,
    confidence=0.65,
    expected_recovery=3250.0,
    expected_value=3235.0,
    explanation="Customer contact selected.",
    evaluated_actions=[],
)

result = execution_service.execute(contact_decision)

print_result(result)


# ------------------------------------------------------------
# TEST 5: Approved escalation
# ------------------------------------------------------------

print_test("Approved Escalation")

escalation_decision = RecoveryDecision(
    case_id="CASE-005",
    recommended_action=RecoveryAction.ESCALATE,
    status=DecisionStatus.APPROVED,
    confidence=0.70,
    expected_recovery=3500.0,
    expected_value=3450.0,
    explanation="Escalation selected.",
    evaluated_actions=[],
)

result = execution_service.execute(escalation_decision)

print_result(result)