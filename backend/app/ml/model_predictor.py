from __future__ import annotations

from pathlib import Path

import joblib

from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)


class RecoveryModelPredictor:
    """
    Load the trained recovery probability ML model and
    predict the probability of successful recovery.
    """

    def __init__(self) -> None:
        backend_directory = Path(__file__).resolve().parents[2]

        model_path = (
            backend_directory
            / "models"
            / "recovery_probability_model.joblib"
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"ML model not found at: {model_path}"
            )

        loaded_artifact = joblib.load(model_path)

        if isinstance(loaded_artifact, dict):
            if "model" not in loaded_artifact:
                raise ValueError(
                    "Saved ML artifact does not contain a 'model' key."
                )

            self.model = loaded_artifact["model"]

            self.feature_count = loaded_artifact.get(
                "feature_count",
                None,
            )
        else:
            self.model = loaded_artifact
            self.feature_count = None

    def _create_features(
        self,
        case: RecoveryCase,
    ) -> list[float]:
        """
        Convert a RecoveryCase into the same 16 ML features
        used during model training.
        """

        payment_status_features = [
            1.0 if case.payment_status is PaymentStatus.FAILED else 0.0,
            1.0
            if case.payment_status is PaymentStatus.RECOVERABLE
            else 0.0,
            1.0
            if case.payment_status is PaymentStatus.RECOVERED
            else 0.0,
            1.0 if case.payment_status is PaymentStatus.EXPIRED else 0.0,
        ]

        failure_reason_features = [
            1.0
            if case.failure_reason
            is FailureReason.INSUFFICIENT_FUNDS
            else 0.0,
            1.0
            if case.failure_reason
            is FailureReason.CARD_DECLINED
            else 0.0,
            1.0
            if case.failure_reason
            is FailureReason.NETWORK_ERROR
            else 0.0,
            1.0
            if case.failure_reason
            is FailureReason.AUTHENTICATION_FAILED
            else 0.0,
            1.0
            if case.failure_reason
            is FailureReason.PAYMENT_METHOD_EXPIRED
            else 0.0,
            1.0
            if case.failure_reason
            is FailureReason.UNKNOWN
            else 0.0,
        ]

        return [
            float(case.amount),
            float(case.failure_count),
            float(case.customer_attempt_count),
            float(case.days_since_failure),
            float(case.is_customer_active),
            float(case.has_valid_payment_method),
            *payment_status_features,
            *failure_reason_features,
        ]

    def predict_recovery_probability(
        self,
        case: RecoveryCase,
    ) -> float:
        """
        Predict the probability that the recovery case
        will be successfully recovered.
        """

        features = self._create_features(case)

        if (
            self.feature_count is not None
            and len(features) != self.feature_count
        ):
            raise ValueError(
                "Feature count mismatch. "
                f"Model expects {self.feature_count} features "
                f"but received {len(features)}."
            )

        probabilities = self.model.predict_proba(
            [features]
        )

        recovery_probability = float(
            probabilities[0][1]
        )

        return round(
            max(
                0.0,
                min(recovery_probability, 1.0),
            ),
            4,
        )
