from pathlib import Path

import pytest

from app.evaluation.dataset_loader import DatasetValidationError, EvaluationCase, load_cases
from app.evaluation.metrics import PerCaseResult, aggregate_metrics
from app.evaluation.outcome_simulator import OutcomeSimulator
from app.evaluation.runner import EvaluationRunner
from app.evaluation.strategies import (
    AlwaysContactStrategy,
    AlwaysEscalateStrategy,
    AlwaysRetryStrategy,
    DoNothingStrategy,
    ReclaimHybridStrategy,
)
from app.models.case import FailureReason, PaymentStatus, RecoveryCase
from app.models.decision import RecoveryAction
from generate_dataset import derive_scenarios, generate_cases, write_cases


def make_case() -> RecoveryCase:
    return RecoveryCase(case_id="TEST-CASE-1", customer_id="CUSTOMER-1", amount=5000, currency="INR", payment_status=PaymentStatus.FAILED, failure_reason=FailureReason.NETWORK_ERROR, failure_count=1, customer_attempt_count=0, days_since_failure=1, is_customer_active=True, has_valid_payment_method=True)


def test_dataset_generation_is_reproducible_valid_and_covered() -> None:
    records = generate_cases(1000, 42)
    assert records == generate_cases(1000, 42)
    assert records != generate_cases(1000, 43)
    assert all(int(record["customer_attempt_count"]) <= int(record["failure_count"]) for record in records)
    labels = {label for record in records for label in str(record["scenario_labels"]).split("|")}
    assert {"RETRY_FAVORABLE", "CONTACT_FAVORABLE", "ESCALATION_FAVORABLE", "NO_ACTION_FAVORABLE", "POLICY_BLOCKED", "HIGH_VALUE", "LOW_VALUE", "RECENT_FAILURE", "AGED_FAILURE"} <= labels


def test_loader_validates_required_fields_and_preserves_scenarios(tmp_path: Path) -> None:
    path = tmp_path / "cases.csv"
    write_cases(path, count=4, seed=42)
    cases = load_cases(path)
    assert len(cases) == 4
    assert isinstance(cases[0], EvaluationCase)
    assert cases[0].scenarios
    path.write_text("case_id\nmissing-fields\n", encoding="utf-8")
    with pytest.raises(DatasetValidationError):
        load_cases(path)


def test_outcome_simulator_is_reproducible_bounded_and_seeded() -> None:
    case = make_case()
    first = OutcomeSimulator(42).simulate(case, RecoveryAction.RETRY_PAYMENT)
    assert first == OutcomeSimulator(42).simulate(case, RecoveryAction.RETRY_PAYMENT)
    different_seed_outcomes = [
        OutcomeSimulator(43).simulate(case, action)
        for action in RecoveryAction
    ]
    assert any(first != outcome for outcome in different_seed_outcomes)
    assert 0 <= first.probability <= 1
    assert first.recovered_amount in {0, case.amount}


def test_strategies_select_expected_actions() -> None:
    case = make_case()
    assert ReclaimHybridStrategy().decide(case).selected_action in RecoveryAction
    assert AlwaysRetryStrategy().decide(case).selected_action is RecoveryAction.RETRY_PAYMENT
    assert AlwaysContactStrategy().decide(case).selected_action is RecoveryAction.CONTACT_CUSTOMER
    assert AlwaysEscalateStrategy().decide(case).selected_action is RecoveryAction.ESCALATE
    assert DoNothingStrategy().decide(case).allowed is True


def test_runner_evaluates_scenarios_and_multi_seed_results(tmp_path: Path) -> None:
    dataset_path = tmp_path / "cases.csv"
    write_cases(dataset_path, count=20, seed=42)
    cases = load_cases(dataset_path)
    small_cases = cases[:20]
    first = EvaluationRunner(seed=7).run(small_cases)
    second = EvaluationRunner(seed=7).run(small_cases)
    multi = EvaluationRunner(seed=7).run_many(small_cases, [7, 8, 9])
    assert first.to_dict() == second.to_dict()
    assert len(first.strategy_results) == 5
    assert len(first.per_case_results) == 100
    assert first.scenario_results
    assert multi.dataset_size == 20
    assert all(metrics.minimum_net_value <= metrics.mean_net_value <= metrics.maximum_net_value for metrics in multi.strategy_results.values())
    assert all(result.regret >= 0 and result.normalized_regret >= 0 for result in first.per_case_results)
    assert first.best_baseline_strategy is not None
    assert first.incremental_recovered_amount == pytest.approx(first.strategy_results["RECLAIM Hybrid"].total_recovered_amount - first.strategy_results[first.best_baseline_strategy].total_recovered_amount)


def test_blocked_baseline_is_recorded_as_violation() -> None:
    case = RecoveryCase(case_id="HIGH-FAILURES", customer_id="CUSTOMER-2", amount=500, currency="INR", payment_status=PaymentStatus.FAILED, failure_reason=FailureReason.INSUFFICIENT_FUNDS, failure_count=8, customer_attempt_count=0, days_since_failure=1, is_customer_active=True, has_valid_payment_method=False)
    result = EvaluationRunner(seed=42, strategies=[AlwaysRetryStrategy()]).run([case])
    metrics = result.strategy_results["Always Retry"]
    assert metrics.policy_violations == 1
    assert metrics.policy_compliance_rate == 0
    assert result.per_case_results[0].allowed is False


def test_scenario_labels_are_feature_derived() -> None:
    record = {"amount": 20000, "failure_count": 1, "customer_attempt_count": 0, "days_since_failure": 2, "is_customer_active": True, "has_valid_payment_method": True}
    assert "HIGH_VALUE" in derive_scenarios(record)
    assert "ESCALATION_FAVORABLE" in derive_scenarios(record)
    assert "RECENT_FAILURE" in derive_scenarios(record)
