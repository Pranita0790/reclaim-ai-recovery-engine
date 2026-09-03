from app.evaluation.metrics import PerCaseResult, aggregate_metrics


def case(**overrides) -> PerCaseResult:
    values = {
        "case_id": "CASE-1",
        "strategy": "Test",
        "scenarios": ("MIXED",),
        "attempted_amount": 100.0,
        "case_amount": 100.0,
        "selected_action": "RETRY_PAYMENT",
        "allowed": True,
        "expected_recovery": 80.0,
        "expected_value": 78.0,
        "recovered": True,
        "recovered_amount": 100.0,
        "action_cost": 2.0,
        "realized_net_value": 98.0,
        "regret": 0.0,
        "normalized_regret": 0.0,
        "expected_recovery_absolute_error": 20.0,
        "expected_value_absolute_error": 20.0,
        "outcome_reason": "success",
    }
    values.update(overrides)
    return PerCaseResult(**values)


def test_aggregate_metrics_calculates_totals_and_rates() -> None:
    metrics = aggregate_metrics("Test", [case(), case(case_id="CASE-2", recovered=False, recovered_amount=0.0, realized_net_value=-2.0, regret=12.0)])
    assert metrics.total_cases == 2
    assert metrics.recovered_cases == 1
    assert metrics.case_recovery_rate == 0.5
    assert metrics.attempt_rate == 1.0
    assert metrics.attempt_recovery_rate == 0.5
    assert metrics.total_attempted_amount == 200.0
    assert metrics.total_recovered_amount == 100.0
    assert metrics.total_net_value == 96.0
    assert metrics.total_regret == 12.0
    assert metrics.regret_rate == 0.5
    assert metrics.policy_compliance_rate == 1.0
    assert metrics.expected_recovery_absolute_error == 20.0
    assert metrics.expected_value_absolute_error == 20.0


def test_aggregate_metrics_is_safe_for_zero_cases() -> None:
    metrics = aggregate_metrics("Empty", [])
    assert metrics.total_cases == 0
    assert metrics.case_recovery_rate == 0.0
    assert metrics.attempt_rate == 0.0
    assert metrics.attempt_recovery_rate == 0.0
    assert metrics.average_net_value_per_case == 0.0
    assert metrics.average_expected_value == 0.0
    assert metrics.average_regret == 0.0
