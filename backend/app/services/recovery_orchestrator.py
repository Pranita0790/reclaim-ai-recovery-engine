from __future__ import annotations

from app.models.audit import AuditEvent, AuditEventType
from app.models.case import PaymentStatus, RecoveryCase
from app.models.decision import RecoveryDecision
from app.models.execution import ExecutionResult, ExecutionStatus
from app.services.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.services.decision_engine import DecisionEngine
from app.services.execution_service import ExecutionService
from app.state_machine.recovery_state_machine import (
    RecoveryState,
    RecoveryStateMachine,
)


class RecoveryWorkflowResult:
    """Container for the complete recovery workflow result."""

    def __init__(
        self,
        case: RecoveryCase,
        decision: RecoveryDecision,
        execution: ExecutionResult,
        final_state: RecoveryState,
        audit_events: list[AuditEvent],
    ) -> None:
        self.case = case
        self.decision = decision
        self.execution = execution
        self.final_state = final_state
        self.audit_events = audit_events


class RecoveryOrchestrator:
    """
    Coordinate the complete recovery workflow.

    Flow:

        Case
          -> State evaluation
          -> Decision
          -> Execution
          -> Final state
          -> Audit trail
    """

    def __init__(
        self,
        decision_engine: DecisionEngine | None = None,
        execution_service: ExecutionService | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.decision_engine = (
            decision_engine or DecisionEngine()
        )

        self.execution_service = (
            execution_service or ExecutionService()
        )

        # Use SQLite-backed audit storage by default.
        self.audit_service = (
            audit_service
            or AuditService(
                repository=AuditRepository()
            )
        )

    def process(
        self,
        case: RecoveryCase,
    ) -> RecoveryWorkflowResult:
        """Run the complete recovery workflow."""

        state_machine = RecoveryStateMachine()

        # --------------------------------------------------
        # CASE RECEIVED
        # --------------------------------------------------

        self.audit_service.record_event(
            case_id=case.case_id,
            event_type=AuditEventType.CASE_RECEIVED,
            message=(
                "Recovery case received by the "
                "orchestration workflow."
            ),
        )

        # --------------------------------------------------
        # CASE STATE EVALUATION
        # --------------------------------------------------

        if (
            case.payment_status is PaymentStatus.EXPIRED
            or case.days_since_failure > 30
        ):
            state_machine.transition(
                RecoveryState.EXPIRED
            )

            self.audit_service.record_event(
                case_id=case.case_id,
                event_type=AuditEventType.POLICY_EVALUATED,
                message=(
                    "Recovery case marked as expired."
                ),
            )

            decision = self.decision_engine.decide(
                case
            )

            execution = self.execution_service.execute(
                decision
            )

            return RecoveryWorkflowResult(
                case=case,
                decision=decision,
                execution=execution,
                final_state=state_machine.state,
                audit_events=(
                    self.audit_service.get_case_events(
                        case.case_id
                    )
                ),
            )

        # --------------------------------------------------
        # CASE IS RECOVERABLE
        # --------------------------------------------------

        state_machine.transition(
            RecoveryState.RECOVERABLE
        )

        self.audit_service.record_event(
            case_id=case.case_id,
            event_type=AuditEventType.POLICY_EVALUATED,
            message=(
                "Recovery case is eligible for evaluation."
            ),
        )

        # --------------------------------------------------
        # DECISION
        # --------------------------------------------------

        decision = self.decision_engine.decide(
            case
        )

        self.audit_service.record_event(
            case_id=case.case_id,
            event_type=AuditEventType.DECISION_CREATED,
            message="Recovery decision created.",
            data={
                "recommended_action": (
                    decision.recommended_action.value
                ),
                "status": decision.status.value,
                "ml_recovery_probability": (
                    decision.ml_recovery_probability
                ),
                "final_action_probability": (
                    decision.confidence
                ),
                "expected_value": (
                    decision.expected_value
                ),
            },
        )

        state_machine.transition(
            RecoveryState.DECISION_MADE
        )

        # --------------------------------------------------
        # EXECUTION START
        # --------------------------------------------------

        state_machine.transition(
            RecoveryState.EXECUTING
        )

        self.audit_service.record_event(
            case_id=case.case_id,
            event_type=AuditEventType.EXECUTION_STARTED,
            message=(
                f"Executing "
                f"{decision.recommended_action.value}."
            ),
        )

        # --------------------------------------------------
        # EXECUTION
        # --------------------------------------------------

        execution = self.execution_service.execute(
            decision
        )

        # --------------------------------------------------
        # EXECUTION RESULT
        # --------------------------------------------------

        if execution.status is ExecutionStatus.SUCCESS:

            state_machine.transition(
                RecoveryState.RECOVERED
            )

            self.audit_service.record_event(
                case_id=case.case_id,
                event_type=(
                    AuditEventType.EXECUTION_COMPLETED
                ),
                message=execution.message,
                data={
                    "execution_id": (
                        execution.execution_id
                    ),
                    "external_reference": (
                        execution.external_reference
                    ),
                },
            )

        else:

            state_machine.transition(
                RecoveryState.FAILED
            )

            self.audit_service.record_event(
                case_id=case.case_id,
                event_type=(
                    AuditEventType.EXECUTION_FAILED
                ),
                message=execution.message,
                data={
                    "execution_status": (
                        execution.status.value
                    ),
                },
            )

        # --------------------------------------------------
        # RETURN COMPLETE WORKFLOW RESULT
        # --------------------------------------------------

        return RecoveryWorkflowResult(
            case=case,
            decision=decision,
            execution=execution,
            final_state=state_machine.state,
            audit_events=(
                self.audit_service.get_case_events(
                    case.case_id
                )
            ),
        )