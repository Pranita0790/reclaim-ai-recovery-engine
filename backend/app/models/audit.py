from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    CASE_RECEIVED = "CASE_RECEIVED"
    BASELINE_ESTIMATED = "BASELINE_ESTIMATED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    ACTION_EVALUATED = "ACTION_EVALUATED"
    DECISION_CREATED = "DECISION_CREATED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


class AuditEvent(BaseModel):
    event_id: str

    case_id: str

    event_type: AuditEventType

    message: str

    data: dict = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)