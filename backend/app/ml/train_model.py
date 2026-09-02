from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
)
from sklearn.model_selection import train_test_split

from app.ml.feature_engineering import FeatureEngineering
from app.ml.training_data import (
    RecoveryTrainingDataGenerator,
)
from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)


MODEL_DIRECTORY = Path("models")
MODEL_PATH = MODEL_DIRECTORY / "recovery_probability_model.joblib"


def create_recovery_case(
    record: dict,
    index: int,
) -> RecoveryCase:
    """Convert a generated training record into a RecoveryCase."""

    return RecoveryCase(
        case_id=f"TRAIN-{index}",
        customer_id=f"CUSTOMER-{index}",
        amount=record["amount"],
        currency="INR",
        payment_status=record["payment_status"],
        failure_reason=record["failure_reason"],
        failure_count=record["failure_count"],
        customer_attempt_count=record[
            "customer_attempt_count"
        ],
        days_since_failure=record[
            "days_since_failure"
        ],
        is_customer_active=record[
            "is_customer_active"
        ],
        has_valid_payment_method=record[
            "has_valid_payment_method"
        ],
    )


def train() -> None:
    """Generate training data and train the recovery model."""

    generator = RecoveryTrainingDataGenerator(
        seed=42,
    )

    records, labels = generator.generate(
        sample_count=5000,
    )

    feature_engineering = FeatureEngineering()

    features = []

    for index, record in enumerate(records):
        case = create_recovery_case(
            record,
            index,
        )

        feature_vector = (
            feature_engineering.transform(case)
        )

        features.append(feature_vector)

    X = np.array(features)
    y = np.array(labels)

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y,
        )
    )

    model = LogisticRegression(
        max_iter=2000,
        random_state=42,
    )

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    print("\nMODEL TRAINING COMPLETE")
    print(
        f"Training samples: {len(X_train)}"
    )
    print(
        f"Test samples: {len(X_test)}"
    )
    print(
        f"Accuracy: {accuracy:.4f}"
    )

    print("\nCLASSIFICATION REPORT")
    print(
        classification_report(
            y_test,
            predictions,
        )
    )

    MODEL_DIRECTORY.mkdir(
        exist_ok=True
    )

    joblib.dump(
        {
            "model": model,
            "feature_count": (
                feature_engineering.feature_count
            ),
        },
        MODEL_PATH,
    )

    print(
        f"\nModel saved to: {MODEL_PATH}"
    )


if __name__ == "__main__":
    train()