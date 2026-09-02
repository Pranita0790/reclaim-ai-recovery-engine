from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.audit import AuditEventType
from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)
from app.models.decision import (
    DecisionStatus,
    RecoveryAction,
)
from app.models.execution import ExecutionStatus
from app.state_machine.recovery_state_machine import RecoveryState


# --------------------------------------------------
# RECOVERY PROCESS REQUEST
# --------------------------------------------------

class RecoveryProcessRequest(BaseModel):
    """Request body used to process a recovery case."""

    case_id: str = Field(
        ...,
        min_length=1,
    )

    customer_id: str = Field(
        ...,
        min_length=1,
    )

    amount: float = Field(
        ...,
        gt=0,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    payment_status: PaymentStatus

    failure_reason: FailureReason

    failure_count: int = Field(
        default=1,
        ge=0,
    )

    customer_attempt_count: int = Field(
        default=0,
        ge=0,
    )

    days_since_failure: int = Field(
        default=0,
        ge=0,
    )

    is_customer_active: bool = True

    has_valid_payment_method: bool = True

    metadata: dict[
        str,
        str | int | float | bool,
    ] = Field(
        default_factory=dict
    )

    def to_recovery_case(self) -> RecoveryCase:
        """Convert the API request into the domain model."""

        return RecoveryCase(
            case_id=self.case_id,
            customer_id=self.customer_id,
            amount=self.amount,
            currency=self.currency,
            payment_status=self.payment_status,
            failure_reason=self.failure_reason,
            failure_count=self.failure_count,
            customer_attempt_count=(
                self.customer_attempt_count
            ),
            days_since_failure=(
                self.days_since_failure
            ),
            is_customer_active=(
                self.is_customer_active
            ),
            has_valid_payment_method=(
                self.has_valid_payment_method
            ),
            metadata=self.metadata,
        )


# --------------------------------------------------
# EVALUATED ACTION RESPONSE
# --------------------------------------------------

class EvaluatedActionResponse(BaseModel):
    """Single recovery action evaluated by the decision engine."""

    action: RecoveryAction

    is_allowed: bool

    success_probability: float

    expected_recovery: float

    expected_value: float

    reason: str


# --------------------------------------------------
# RECOVERY PROCESS RESPONSE
# --------------------------------------------------

class RecoveryProcessResponse(BaseModel):
    """Response returned after processing a recovery case."""

    # Final decision

    case_id: str

    recommended_action: RecoveryAction

    decision_status: DecisionStatus

    confidence: float

    expected_recovery: float

    expected_value: float

    explanation: str

    # Decision intelligence

    ml_recovery_probability: float

    decision_source: str

    policy_checks: list[str]

    evaluated_actions: list[
        EvaluatedActionResponse
    ]

    # Execution

    execution_status: ExecutionStatus

    execution_message: str

    external_reference: str | None = None

    final_state: RecoveryState


# --------------------------------------------------
# ERROR RESPONSE
# --------------------------------------------------

class ErrorResponse(BaseModel):
    """Standard API error response."""

    error: str = Field(
        ...,
        examples=[
            "BUSINESS_VALIDATION_ERROR"
        ],
    )

    message: str = Field(
        ...,
        examples=[
            (
                "Recovery case amount must "
                "be greater than zero."
            )
        ],
    )

    detail: Any | None = None


# --------------------------------------------------
# AUDIT EVENT RESPONSE
# --------------------------------------------------

class AuditEventResponse(BaseModel):
    """Single audit event returned by the API."""

    event_id: str

    case_id: str

    event_type: AuditEventType

    message: str

    data: dict[str, Any]

    created_at: datetime


# --------------------------------------------------
# AUDIT TRAIL RESPONSE
# --------------------------------------------------

class AuditTrailResponse(BaseModel):
    """Audit trail returned for a recovery case."""

    case_id: str

    events: list[AuditEventResponse]