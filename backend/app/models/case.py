from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    FAILED = "FAILED"
    RECOVERABLE = "RECOVERABLE"
    RECOVERED = "RECOVERED"
    EXPIRED = "EXPIRED"


class FailureReason(str, Enum):
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    CARD_DECLINED = "CARD_DECLINED"
    NETWORK_ERROR = "NETWORK_ERROR"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    PAYMENT_METHOD_EXPIRED = "PAYMENT_METHOD_EXPIRED"
    UNKNOWN = "UNKNOWN"


class RecoveryCase(BaseModel):
    case_id: str = Field(..., min_length=1)

    customer_id: str = Field(..., min_length=1)

    amount: float = Field(..., gt=0)

    currency: str = Field(default="INR", min_length=3, max_length=3)

    payment_status: PaymentStatus

    failure_reason: FailureReason

    failure_count: int = Field(default=1, ge=0)

    customer_attempt_count: int = Field(default=0, ge=0)

    days_since_failure: int = Field(default=0, ge=0)

    is_customer_active: bool = True

    has_valid_payment_method: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)

    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)