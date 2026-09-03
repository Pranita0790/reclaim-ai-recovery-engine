from __future__ import annotations

from dataclasses import dataclass

from app.models.case import RecoveryCase
from app.models.decision import RecoveryAction


@dataclass(frozen=True)
class ReplayCase:
    case_id: str
    customer_id: str
    amount: float
    currency: str
    payment_status: str
    failure_reason: str
    failure_count: int
    customer_attempt_count: int
    days_since_failure: int
    is_customer_active: bool
    has_valid_payment_method: bool
    scenario_labels: tuple[str, ...]

    @classmethod
    def from_case(cls, case: RecoveryCase, scenarios: tuple[str, ...]) -> ReplayCase:
        return cls(
            case_id=case.case_id,
            customer_id=case.customer_id,
            amount=case.amount,
            currency=case.currency,
            payment_status=case.payment_status.value,
            failure_reason=case.failure_reason.value,
            failure_count=case.failure_count,
            customer_attempt_count=case.customer_attempt_count,
            days_since_failure=case.days_since_failure,
            is_customer_active=case.is_customer_active,
            has_valid_payment_method=case.has_valid_payment_method,
            scenario_labels=scenarios,
        )


@dataclass(frozen=True)
class ReplayDecision:
    selected_action: RecoveryAction
    decision_status: str
    confidence: float
    ml_recovery_probability: float
    decision_source: str
    explanation: str


@dataclass(frozen=True)
class ReplayCandidate:
    action: RecoveryAction
    is_allowed: bool
    policy_reason: str
    success_probability: float
    expected_recovery: float
    expected_value: float
    action_cost: float
    recovered: bool
    recovered_amount: float
    realized_net_value: float
    outcome_reason: str
    is_selected: bool


@dataclass(frozen=True)
class ReplayResult:
    case: ReplayCase
    strategy: str
    seed: int
    decision: ReplayDecision
    candidates: tuple[ReplayCandidate, ...]
    regret: float
    best_realized_action: RecoveryAction
    best_realized_net_value: float
