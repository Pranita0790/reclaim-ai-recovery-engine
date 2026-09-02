from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.decision import RecoveryAction


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ExecutionResult(BaseModel):
    execution_id: str

    case_id: str

    action: RecoveryAction

    status: ExecutionStatus

    idempotency_key: str

    message: str

    external_reference: str | None = None

    executed_at: datetime = Field(default_factory=datetime.utcnow)