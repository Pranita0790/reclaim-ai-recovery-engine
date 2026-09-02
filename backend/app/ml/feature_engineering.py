from __future__ import annotations

from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)


class FeatureEngineering:
    """
    Convert RecoveryCase objects into stable numerical feature vectors
    for the machine learning recovery probability model.
    """

    FAILURE_REASON_VALUES = list(FailureReason)
    PAYMENT_STATUS_VALUES = list(PaymentStatus)

    def transform(
        self,
        case: RecoveryCase,
    ) -> list[float]:
        """
        Convert a recovery case into a numerical feature vector.

        IMPORTANT:
        The feature order must remain unchanged because the trained
        machine learning model depends on this exact ordering.
        """

        numerical_features = [
            float(case.amount),
            float(case.failure_count),
            float(case.customer_attempt_count),
            float(case.days_since_failure),
            1.0 if case.is_customer_active else 0.0,
            1.0 if case.has_valid_payment_method else 0.0,
        ]

        failure_reason_features = [
            1.0 if case.failure_reason == reason else 0.0
            for reason in self.FAILURE_REASON_VALUES
        ]

        payment_status_features = [
            1.0 if case.payment_status == status else 0.0
            for status in self.PAYMENT_STATUS_VALUES
        ]

        return (
            numerical_features
            + failure_reason_features
            + payment_status_features
        )

    @property
    def feature_count(self) -> int:
        """Return the number of features generated."""

        return (
            6
            + len(self.FAILURE_REASON_VALUES)
            + len(self.PAYMENT_STATUS_VALUES)
        )