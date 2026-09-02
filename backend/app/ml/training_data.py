from __future__ import annotations

import random

from app.models.case import (
    FailureReason,
    PaymentStatus,
)


class RecoveryTrainingDataGenerator:
    """
    Generate synthetic recovery data for development and demonstration.

    The generated labels simulate whether a payment recovery attempt
    would eventually succeed.
    """

    def __init__(
        self,
        seed: int = 42,
    ) -> None:
        self.random = random.Random(seed)

    def generate(
        self,
        sample_count: int = 5000,
    ) -> tuple[list[dict], list[int]]:
        """
        Generate synthetic training features and binary labels.

        Label:
            1 -> recovery successful
            0 -> recovery unsuccessful
        """

        records: list[dict] = []
        labels: list[int] = []

        for _ in range(sample_count):
            record = self._generate_record()

            probability = self._calculate_recovery_probability(
                record
            )

            recovered = (
                1
                if self.random.random() < probability
                else 0
            )

            records.append(record)
            labels.append(recovered)

        return records, labels

    def _generate_record(self) -> dict:
        """Generate one synthetic recovery case."""

        return {
            "amount": round(
                self.random.uniform(100, 50000),
                2,
            ),
            "failure_count": self.random.randint(0, 8),
            "customer_attempt_count": self.random.randint(
                0,
                5,
            ),
            "days_since_failure": self.random.randint(
                0,
                60,
            ),
            "is_customer_active": self.random.choice(
                [True, True, True, False]
            ),
            "has_valid_payment_method": self.random.choice(
                [True, True, True, True, False]
            ),
            "failure_reason": self.random.choice(
                list(FailureReason)
            ),
            "payment_status": self.random.choice(
                [
                    PaymentStatus.FAILED,
                    PaymentStatus.RECOVERABLE,
                    PaymentStatus.RECOVERED,
                    PaymentStatus.EXPIRED,
                ]
            ),
        }

    def _calculate_recovery_probability(
        self,
        record: dict,
    ) -> float:
        """
        Simulate a recovery probability using business assumptions.

        This creates learnable patterns for ML demonstration.
        """

        probability = 0.50

        # Customer activity strongly improves recovery.
        if record["is_customer_active"]:
            probability += 0.18
        else:
            probability -= 0.20

        # A valid payment method significantly improves recovery.
        if record["has_valid_payment_method"]:
            probability += 0.20
        else:
            probability -= 0.30

        # Older failures are harder to recover.
        days_since_failure = record[
            "days_since_failure"
        ]

        probability -= min(
            days_since_failure * 0.008,
            0.40,
        )

        # Repeated failures reduce recovery probability.
        probability -= min(
            record["failure_count"] * 0.04,
            0.25,
        )

        # Too many customer attempts reduce probability.
        probability -= min(
            record["customer_attempt_count"] * 0.03,
            0.15,
        )

        # Failure reason effects.
        reason = record["failure_reason"]

        if reason is FailureReason.NETWORK_ERROR:
            probability += 0.15

        elif reason is FailureReason.INSUFFICIENT_FUNDS:
            probability += 0.03

        elif reason is FailureReason.CARD_DECLINED:
            probability -= 0.08

        elif reason is FailureReason.AUTHENTICATION_FAILED:
            probability -= 0.12

        elif reason is FailureReason.PAYMENT_METHOD_EXPIRED:
            probability -= 0.25

        elif reason is FailureReason.UNKNOWN:
            probability -= 0.05

        # Payment state effects.
        status = record["payment_status"]

        if status is PaymentStatus.RECOVERABLE:
            probability += 0.10

        elif status is PaymentStatus.FAILED:
            probability -= 0.05

        elif status is PaymentStatus.EXPIRED:
            probability -= 0.50

        elif status is PaymentStatus.RECOVERED:
            probability += 0.30

        # Small random variation prevents perfectly deterministic data.
        probability += self.random.uniform(
            -0.08,
            0.08,
        )

        # Keep probability valid.
        return max(
            0.01,
            min(probability, 0.99),
        )