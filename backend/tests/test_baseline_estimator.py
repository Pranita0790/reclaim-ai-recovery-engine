from math import isclose

from app.core.constants import BASE_SUCCESS_PROBABILITIES
from app.models.case import FailureReason, RecoveryCase
from app.models.decision import RecoveryAction
from app.services.baseline_estimator import BaselineEstimator


def test_retry_payment_uses_case_signals() -> None:
    case = RecoveryCase(
        case_id="case-1",
        customer_id="customer-1",
        amount=500.0,
        payment_status="FAILED",
        failure_reason=FailureReason.NETWORK_ERROR,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=3,
        is_customer_active=True,
        has_valid_payment_method=True,
    )

    estimator = BaselineEstimator()
    probability = estimator.estimate(case, RecoveryAction.RETRY_PAYMENT)

    expected = BASE_SUCCESS_PROBABILITIES[RecoveryAction.RETRY_PAYMENT]
    expected += 0.12 + 0.08 - 0.04 - 0.06

    assert isclose(probability, expected, abs_tol=1e-9)


def test_contact_customer_uses_customer_signals() -> None:
    case = RecoveryCase(
        case_id="case-2",
        customer_id="customer-2",
        amount=1000.0,
        payment_status="FAILED",
        failure_reason=FailureReason.UNKNOWN,
        failure_count=2,
        customer_attempt_count=2,
        days_since_failure=5,
        is_customer_active=True,
        has_valid_payment_method=False,
    )

    probability = BaselineEstimator().estimate(case, RecoveryAction.CONTACT_CUSTOMER)

    expected = BASE_SUCCESS_PROBABILITIES[RecoveryAction.CONTACT_CUSTOMER]
    expected += 0.10 - 0.14 - 0.10

    assert isclose(probability, expected, abs_tol=1e-9)


def test_do_nothing_is_zero() -> None:
    case = RecoveryCase(
        case_id="case-3",
        customer_id="customer-3",
        amount=2500.0,
        payment_status="FAILED",
        failure_reason=FailureReason.INSUFFICIENT_FUNDS,
        failure_count=5,
        customer_attempt_count=1,
        days_since_failure=10,
        is_customer_active=False,
        has_valid_payment_method=False,
    )

    assert BaselineEstimator().estimate(case, RecoveryAction.DO_NOTHING) == 0.0


def test_escalate_increases_with_amount() -> None:
    case = RecoveryCase(
        case_id="case-4",
        customer_id="customer-4",
        amount=2000.0,
        payment_status="FAILED",
        failure_reason=FailureReason.CARD_DECLINED,
        failure_count=1,
        customer_attempt_count=0,
        days_since_failure=2,
        is_customer_active=True,
        has_valid_payment_method=True,
    )

    probability = BaselineEstimator().estimate(case, RecoveryAction.ESCALATE)

    expected = BASE_SUCCESS_PROBABILITIES[RecoveryAction.ESCALATE] + 0.08

    assert isclose(probability, expected, abs_tol=1e-9)
