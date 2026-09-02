from __future__ import annotations

from app.core.constants import BASE_SUCCESS_PROBABILITIES
from app.models.case import FailureReason, RecoveryCase
from app.models.decision import RecoveryAction


class BaselineEstimator:
    """
    Estimate action success probability using deterministic
    business and case signals.
    """

    @staticmethod
    def _clamp_probability(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _retry_payment_adjustment(
        case: RecoveryCase,
    ) -> float:
        adjustment = 0.0

        if case.has_valid_payment_method:
            adjustment += 0.12

        if case.failure_reason is FailureReason.NETWORK_ERROR:
            adjustment += 0.08

        elif (
            case.failure_reason
            is FailureReason.INSUFFICIENT_FUNDS
        ):
            adjustment -= 0.10

        adjustment -= (
            0.04 * min(case.failure_count, 5)
        )

        adjustment -= (
            0.02 * min(case.days_since_failure, 10)
        )

        return adjustment

    @staticmethod
    def _contact_customer_adjustment(
        case: RecoveryCase,
    ) -> float:
        adjustment = 0.0

        if case.is_customer_active:
            adjustment += 0.10

        adjustment -= (
            0.07
            * min(case.customer_attempt_count, 4)
        )

        adjustment -= (
            0.02
            * min(case.days_since_failure, 10)
        )

        return adjustment

    @staticmethod
    def _escalate_adjustment(
        case: RecoveryCase,
    ) -> float:
        return min(
            0.12,
            0.04 + (case.amount / 50000.0),
        )

    def estimate(
        self,
        case: RecoveryCase,
        action: RecoveryAction,
    ) -> float:
        """
        Return a deterministic baseline success probability
        for a given recovery action.
        """

        if action is RecoveryAction.DO_NOTHING:
            return 0.0

        probability = BASE_SUCCESS_PROBABILITIES[
            action
        ]

        if action is RecoveryAction.RETRY_PAYMENT:
            probability += (
                self._retry_payment_adjustment(case)
            )

        elif action is RecoveryAction.CONTACT_CUSTOMER:
            probability += (
                self._contact_customer_adjustment(case)
            )

        elif action is RecoveryAction.ESCALATE:
            probability += (
                self._escalate_adjustment(case)
            )

        return self._clamp_probability(probability)