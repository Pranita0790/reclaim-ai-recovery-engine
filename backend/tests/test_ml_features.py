from app.ml.feature_engineering import FeatureEngineering
from app.models.case import (
    FailureReason,
    PaymentStatus,
    RecoveryCase,
)


def test_feature_engineering():

    case = RecoveryCase(
        case_id="ML-TEST-001",
        customer_id="CUSTOMER-001",
        amount=5000,
        payment_status=PaymentStatus.RECOVERABLE,
        failure_reason=FailureReason.NETWORK_ERROR,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=1,
        is_customer_active=True,
        has_valid_payment_method=True,
    )

    feature_engineering = FeatureEngineering()

    features = feature_engineering.transform(case)

    print("\nML FEATURES")
    print(features)

    print("\nFEATURE COUNT")
    print(feature_engineering.feature_count)

    assert len(features) == feature_engineering.feature_count
    assert len(features) == 16