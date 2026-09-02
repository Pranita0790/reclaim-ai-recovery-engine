from __future__ import annotations

from uuid import uuid4

from app.models.decision import (
    DecisionStatus,
    RecoveryAction,
    RecoveryDecision,
)
from app.models.execution import (
    ExecutionResult,
    ExecutionStatus,
)


class ExecutionService:
    """
    Execute approved recovery decisions.

    This implementation uses deterministic simulated execution
    with in-memory idempotency protection.
    """

    def __init__(self) -> None:
        self._executions: dict[
            str,
            ExecutionResult,
        ] = {}

    def execute(
        self,
        decision: RecoveryDecision,
    ) -> ExecutionResult:
        """Execute the recommended recovery action."""

        idempotency_key = (
            f"{decision.case_id}:"
            f"{decision.recommended_action.value}"
        )

        # --------------------------------------------------
        # IDEMPOTENCY CHECK
        # --------------------------------------------------

        existing_execution = self._executions.get(
            idempotency_key
        )

        if existing_execution is not None:
            return existing_execution

        execution_id = str(uuid4())

        # --------------------------------------------------
        # DECISION NOT APPROVED
        # --------------------------------------------------

        if decision.status is not DecisionStatus.APPROVED:
            result = ExecutionResult(
                execution_id=execution_id,
                case_id=decision.case_id,
                action=decision.recommended_action,
                status=ExecutionStatus.SKIPPED,
                idempotency_key=idempotency_key,
                message=(
                    "Execution skipped because the recovery decision "
                    "was not approved."
                ),
            )

            self._executions[idempotency_key] = result
            return result

        # --------------------------------------------------
        # DO NOTHING
        # --------------------------------------------------

        if decision.recommended_action is RecoveryAction.DO_NOTHING:
            result = ExecutionResult(
                execution_id=execution_id,
                case_id=decision.case_id,
                action=decision.recommended_action,
                status=ExecutionStatus.SKIPPED,
                idempotency_key=idempotency_key,
                message=(
                    "Execution skipped because no recovery action "
                    "was selected."
                ),
            )

            self._executions[idempotency_key] = result
            return result

        # --------------------------------------------------
        # RETRY PAYMENT
        # --------------------------------------------------

        if decision.recommended_action is RecoveryAction.RETRY_PAYMENT:
            result = ExecutionResult(
                execution_id=execution_id,
                case_id=decision.case_id,
                action=decision.recommended_action,
                status=ExecutionStatus.SUCCESS,
                idempotency_key=idempotency_key,
                message="Payment retry executed successfully.",
                external_reference=(
                    f"SIM-PAY-{uuid4().hex[:8].upper()}"
                ),
            )

            self._executions[idempotency_key] = result
            return result

        # --------------------------------------------------
        # CONTACT CUSTOMER
        # --------------------------------------------------

        if decision.recommended_action is RecoveryAction.CONTACT_CUSTOMER:
            result = ExecutionResult(
                execution_id=execution_id,
                case_id=decision.case_id,
                action=decision.recommended_action,
                status=ExecutionStatus.SUCCESS,
                idempotency_key=idempotency_key,
                message=(
                    "Customer recovery contact initiated successfully."
                ),
                external_reference=(
                    f"SIM-CONTACT-{uuid4().hex[:8].upper()}"
                ),
            )

            self._executions[idempotency_key] = result
            return result

        # --------------------------------------------------
        # ESCALATE
        # --------------------------------------------------

        if decision.recommended_action is RecoveryAction.ESCALATE:
            result = ExecutionResult(
                execution_id=execution_id,
                case_id=decision.case_id,
                action=decision.recommended_action,
                status=ExecutionStatus.SUCCESS,
                idempotency_key=idempotency_key,
                message="Recovery case escalated successfully.",
                external_reference=(
                    f"SIM-ESC-{uuid4().hex[:8].upper()}"
                ),
            )

            self._executions[idempotency_key] = result
            return result

        # --------------------------------------------------
        # SAFETY FALLBACK
        # --------------------------------------------------

        result = ExecutionResult(
            execution_id=execution_id,
            case_id=decision.case_id,
            action=decision.recommended_action,
            status=ExecutionStatus.FAILED,
            idempotency_key=idempotency_key,
            message=(
                "Execution failed because the recovery action "
                "is unknown."
            ),
        )

        self._executions[idempotency_key] = result

        return result