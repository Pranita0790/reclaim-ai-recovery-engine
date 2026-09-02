from enum import Enum

from pydantic import BaseModel, Field


class RecoveryAction(str, Enum):
    RETRY_PAYMENT = "RETRY_PAYMENT"
    CONTACT_CUSTOMER = "CONTACT_CUSTOMER"
    ESCALATE = "ESCALATE"
    DO_NOTHING = "DO_NOTHING"


class DecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"


class ActionScore(BaseModel):
    action: RecoveryAction

    success_probability: float = Field(
        ...,
        ge=0,
        le=1,
    )

    expected_recovery: float = Field(
        ...,
        ge=0,
    )

    action_cost: float = Field(
        ...,
        ge=0,
    )

    expected_value: float

    is_allowed: bool

    reason: str


class RecoveryDecision(BaseModel):
    case_id: str

    recommended_action: RecoveryAction

    status: DecisionStatus

    confidence: float = Field(
        ...,
        ge=0,
        le=1,
    )

    expected_recovery: float = Field(
        ...,
        ge=0,
    )

    expected_value: float

    explanation: str

    evaluated_actions: list[ActionScore]

    policy_checks: list[str] = Field(
        default_factory=list
    )

    # ML explainability fields
    ml_recovery_probability: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )

    decision_source: str = Field(
        default="HYBRID_RULES_AND_ML",
    )