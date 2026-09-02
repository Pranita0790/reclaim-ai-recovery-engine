from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.errors import BusinessValidationError
from app.api.schemas import (
    AuditEventResponse,
    AuditTrailResponse,
    ErrorResponse,
    RecoveryProcessRequest,
    RecoveryProcessResponse,
)
from app.services.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.services.recovery_orchestrator import RecoveryOrchestrator


router = APIRouter(
    prefix="/recovery",
    tags=["Recovery"],
)


# --------------------------------------------------
# SHARED AUDIT INFRASTRUCTURE
# --------------------------------------------------

audit_repository = AuditRepository()

audit_service = AuditService(
    repository=audit_repository
)


# --------------------------------------------------
# BUSINESS VALIDATION
# --------------------------------------------------

def validate_business_data(
    request: RecoveryProcessRequest,
) -> None:
    """Validate business rules before processing a recovery case."""

    if (
        request.customer_attempt_count
        > request.failure_count
    ):
        raise BusinessValidationError(
            message=(
                "Customer attempt count cannot exceed "
                "failure count."
            ),
        )

    if request.amount <= 0:
        raise BusinessValidationError(
            message=(
                "Recovery case amount must be greater than zero."
            ),
        )

    if request.failure_count < 0:
        raise BusinessValidationError(
            message=(
                "Failure count cannot be negative."
            ),
        )

    if request.customer_attempt_count < 0:
        raise BusinessValidationError(
            message=(
                "Customer attempt count cannot be negative."
            ),
        )

    if request.days_since_failure < 0:
        raise BusinessValidationError(
            message=(
                "Days since failure cannot be negative."
            ),
        )


# --------------------------------------------------
# PROCESS RECOVERY CASE
# --------------------------------------------------

@router.post(
    "/process",
    response_model=RecoveryProcessResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Business validation error.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected internal server error.",
        },
    },
)
def process_recovery_case(
    request: RecoveryProcessRequest,
) -> RecoveryProcessResponse:
    """Process a recovery case through the complete workflow."""

    validate_business_data(request)

    recovery_case = request.to_recovery_case()

    # Pass the persistent audit service into
    # the orchestrator.
    orchestrator = RecoveryOrchestrator(
        audit_service=audit_service
    )

    result = orchestrator.process(
        recovery_case
    )

    return RecoveryProcessResponse(
        case_id=result.case.case_id,
        recommended_action=(
            result.decision.recommended_action
        ),
        decision_status=result.decision.status,
        confidence=result.decision.confidence,
        expected_recovery=(
            result.decision.expected_recovery
        ),
        expected_value=result.decision.expected_value,
        explanation=result.decision.explanation,
        execution_status=result.execution.status,
        execution_message=result.execution.message,
        external_reference=(
            result.execution.external_reference
        ),
        final_state=result.final_state,
    )


# --------------------------------------------------
# GET CASE AUDIT TRAIL
# --------------------------------------------------

@router.get(
    "/{case_id}/audit",
    response_model=AuditTrailResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "No audit events found for the case.",
        },
    },
)
def get_recovery_audit_trail(
    case_id: str,
) -> AuditTrailResponse:
    """Return the persistent audit trail for a recovery case."""

    events = audit_service.get_case_events(
        case_id
    )

    if not events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No audit events found for case "
                f"'{case_id}'."
            ),
        )

    return AuditTrailResponse(
        case_id=case_id,
        events=[
            AuditEventResponse(
                event_id=event.event_id,
                case_id=event.case_id,
                event_type=event.event_type.value,
                message=event.message,
                data=event.data,
                created_at=event.created_at,
            )
            for event in events
        ],
    )


# --------------------------------------------------
# GET ALL AUDIT EVENTS
# --------------------------------------------------

@router.get(
    "/audit",
    response_model=list[AuditEventResponse],
)
def get_all_audit_events() -> list[AuditEventResponse]:
    """Return every persisted audit event."""

    events = audit_service.get_all_events()

    return [
        AuditEventResponse(
            event_id=event.event_id,
            case_id=event.case_id,
            event_type=event.event_type.value,
            message=event.message,
            data=event.data,
            created_at=event.created_at,
        )
        for event in events
    ]