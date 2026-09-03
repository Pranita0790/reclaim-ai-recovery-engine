from __future__ import annotations

from pydantic import BaseModel


class ReplayCaseResponse(BaseModel):
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
    scenario_labels: list[str]


class ReplayDecisionResponse(BaseModel):
    selected_action: str
    decision_status: str
    confidence: float
    ml_recovery_probability: float
    decision_source: str
    explanation: str


class ReplayCandidateResponse(BaseModel):
    action: str
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


class ReplayResponse(BaseModel):
    case: ReplayCaseResponse
    strategy: str
    seed: int
    decision: ReplayDecisionResponse
    candidates: list[ReplayCandidateResponse]
    regret: float
    best_realized_action: str
    best_realized_net_value: float
