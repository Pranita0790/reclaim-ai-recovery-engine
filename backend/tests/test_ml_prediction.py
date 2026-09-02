from app.ml.model_predictor import (
    RecoveryModelPredictor,
)
from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)


def test_ml_prediction():

    case = RecoveryCase(
        case_id="ML-TEST-001",
        customer_id="CUSTOMER-001",
        amount=5000,
        currency="INR",
        payment_status=PaymentStatus.RECOVERABLE,
        failure_reason=FailureReason.NETWORK_ERROR,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=1,
        is_customer_active=True,
        has_valid_payment_method=True,
    )

    predictor = RecoveryModelPredictor()

    probability = (
        predictor.predict_recovery_probability(case)
    )

    print("\nML RECOVERY PREDICTION")
    print(f"Case ID: {case.case_id}")
    print(f"Recovery Probability: {probability}")

    assert 0.0 <= probability <= 1.0


def test_feature_count():

    case = RecoveryCase(
        case_id="ML-TEST-002",
        customer_id="CUSTOMER-002",
        amount=3000,
        currency="INR",
        payment_status=PaymentStatus.FAILED,
        failure_reason=FailureReason.CARD_DECLINED,
        failure_count=2,
        customer_attempt_count=1,
        days_since_failure=3,
        is_customer_active=True,
        has_valid_payment_method=True,
    )

    predictor = RecoveryModelPredictor()

    features = predictor._create_features(case)

    print("\nML FEATURES")
    print(features)

    print("\nFEATURE COUNT")
    print(len(features))

    assert len(features) == 16