from __future__ import annotations

from app.core.constants import (
    MAX_CUSTOMER_ATTEMPTS,
    MAX_DAYS_FOR_AUTOMATIC_RECOVERY,
    MAX_PAYMENT_RETRIES,
    MIN_AMOUNT_FOR_ESCALATION,
)
from app.models.case import RecoveryCase
from app.models.decision import RecoveryAction


class PolicyEngine:
    """Evaluate whether a recovery action is allowed for a case."""

    def evaluate(
        self,
        case: RecoveryCase,
        action: RecoveryAction,
    ) -> tuple[bool, str]:
        """
        Return:
            (is_allowed, reason)
        """

        # --------------------------------------------------
        # Global policy checks
        # --------------------------------------------------

        if action is RecoveryAction.DO_NOTHING:
            return True, "No action is always allowed."

        if case.days_since_failure > MAX_DAYS_FOR_AUTOMATIC_RECOVERY:
            return (
                False,
                "Automatic recovery window has expired.",
            )

        # --------------------------------------------------
        # RETRY PAYMENT
        # --------------------------------------------------

        if action is RecoveryAction.RETRY_PAYMENT:
            if not case.has_valid_payment_method:
                return (
                    False,
                    "Customer does not have a valid payment method.",
                )

            if case.failure_count >= MAX_PAYMENT_RETRIES:
                return (
                    False,
                    f"Maximum payment retries ({MAX_PAYMENT_RETRIES}) reached.",
                )

            return True, "Payment retry is allowed."

        # --------------------------------------------------
        # CONTACT CUSTOMER
        # --------------------------------------------------

        if action is RecoveryAction.CONTACT_CUSTOMER:
            if not case.is_customer_active:
                return (
                    False,
                    "Customer is not active.",
                )

            if case.customer_attempt_count >= MAX_CUSTOMER_ATTEMPTS:
                return (
                    False,
                    f"Maximum customer contact attempts ({MAX_CUSTOMER_ATTEMPTS}) reached.",
                )

            return True, "Customer contact is allowed."

        # --------------------------------------------------
        # ESCALATE
        # --------------------------------------------------

        if action is RecoveryAction.ESCALATE:
            if case.amount < MIN_AMOUNT_FOR_ESCALATION:
                return (
                    False,
                    (
                        "Amount is below the minimum escalation threshold "
                        f"({MIN_AMOUNT_FOR_ESCALATION})."
                    ),
                )

            return True, "Escalation is allowed."

        # --------------------------------------------------
        # DO NOTHING
        # --------------------------------------------------

        if action is RecoveryAction.DO_NOTHING:
            return True, "No action is always allowed."

        return False, "Unknown recovery action."