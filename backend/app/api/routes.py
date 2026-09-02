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

    # --------------------------------------------------
    # VALIDATE REQUEST
    # --------------------------------------------------

    validate_business_data(request)

    # --------------------------------------------------
    # CONVERT API REQUEST TO DOMAIN MODEL
    # --------------------------------------------------

    recovery_case = request.to_recovery_case()

    # --------------------------------------------------
    # CREATE ORCHESTRATOR
    # --------------------------------------------------

    orchestrator = RecoveryOrchestrator(
        audit_service=audit_service
    )

    # --------------------------------------------------
    # PROCESS RECOVERY CASE
    # --------------------------------------------------

    result = orchestrator.process(
        recovery_case
    )

    # --------------------------------------------------
    # SAFE EXTRACTION OF NEW RESPONSE FIELDS
    #
    # The orchestrator/domain objects may use slightly
    # different attribute names depending on your existing
    # implementation. getattr prevents the API from
    # crashing while keeping the response schema complete.
    # --------------------------------------------------

    ml_recovery_probability = getattr(
        result,
        "ml_recovery_probability",
        None,
    )

    if ml_recovery_probability is None:
        ml_recovery_probability = getattr(
            result.decision,
            "ml_recovery_probability",
            None,
        )

    if ml_recovery_probability is None:
        ml_recovery_probability = getattr(
            result.decision,
            "success_probability",
            result.decision.expected_recovery,
        )

    decision_source = getattr(
        result,
        "decision_source",
        None,
    )

    if decision_source is None:
        decision_source = getattr(
            result.decision,
            "decision_source",
            None,
        )

    if decision_source is None:
        decision_source = "RECOVERY_ENGINE"

    policy_checks = getattr(
        result,
        "policy_checks",
        None,
    )

    if policy_checks is None:
        policy_checks = getattr(
            result.decision,
            "policy_checks",
            [],
        )

    if policy_checks is None:
        policy_checks = []

    evaluated_actions = getattr(
        result,
        "evaluated_actions",
        None,
    )

    if evaluated_actions is None:
        evaluated_actions = getattr(
            result.decision,
            "evaluated_actions",
            [],
        )

    if evaluated_actions is None:
        evaluated_actions = []

    # --------------------------------------------------
    # NORMALIZE EVALUATED ACTIONS
    #
    # Converts domain objects into the structure expected
    # by the API response schema.
    # --------------------------------------------------

    normalized_actions = []

    for action in evaluated_actions:

        if isinstance(action, dict):

            normalized_actions.append(
                {
                    "action": action.get(
                        "action",
                        action.get(
                            "recommended_action",
                            "RETRY_PAYMENT",
                        ),
                    ),
                    "is_allowed": action.get(
                        "is_allowed",
                        True,
                    ),
                    "success_probability": action.get(
                        "success_probability",
                        action.get(
                            "expected_recovery",
                            0.0,
                        ),
                    ),
                    "expected_recovery": action.get(
                        "expected_recovery",
                        0.0,
                    ),
                    "expected_value": action.get(
                        "expected_value",
                        0.0,
                    ),
                    "reason": action.get(
                        "reason",
                        "",
                    ),
                }
            )

        else:

            normalized_actions.append(
                {
                    "action": getattr(
                        action,
                        "action",
                        getattr(
                            action,
                            "recommended_action",
                            "RETRY_PAYMENT",
                        ),
                    ),
                    "is_allowed": getattr(
                        action,
                        "is_allowed",
                        True,
                    ),
                    "success_probability": getattr(
                        action,
                        "success_probability",
                        getattr(
                            action,
                            "expected_recovery",
                            0.0,
                        ),
                    ),
                    "expected_recovery": getattr(
                        action,
                        "expected_recovery",
                        0.0,
                    ),
                    "expected_value": getattr(
                        action,
                        "expected_value",
                        0.0,
                    ),
                    "reason": getattr(
                        action,
                        "reason",
                        "",
                    ),
                }
            )

    # --------------------------------------------------
    # RETURN COMPLETE API RESPONSE
    # --------------------------------------------------

    return RecoveryProcessResponse(
        case_id=result.case.case_id,

        recommended_action=(
            result.decision.recommended_action
        ),

        decision_status=(
            result.decision.status
        ),

        confidence=(
            result.decision.confidence
        ),

        expected_recovery=(
            result.decision.expected_recovery
        ),

        expected_value=(
            result.decision.expected_value
        ),

        explanation=(
            result.decision.explanation
        ),

        # ----------------------------------------------
        # NEW REQUIRED RESPONSE FIELDS
        # ----------------------------------------------

        ml_recovery_probability=(
            ml_recovery_probability
        ),

        decision_source=(
            decision_source
        ),

        policy_checks=(
            policy_checks
        ),

        evaluated_actions=(
            normalized_actions
        ),

        # ----------------------------------------------
        # EXECUTION RESULT
        # ----------------------------------------------

        execution_status=(
            result.execution.status
        ),

        execution_message=(
            result.execution.message
        ),

        external_reference=(
            result.execution.external_reference
        ),

        final_state=(
            result.final_state
        ),
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