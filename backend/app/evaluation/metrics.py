from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class PerCaseResult:
    case_id: str
    strategy: str
    scenarios: tuple[str, ...]
    attempted_amount: float
    case_amount: float
    selected_action: str
    allowed: bool
    expected_recovery: float
    expected_value: float
    recovered: bool
    recovered_amount: float
    action_cost: float
    realized_net_value: float
    regret: float
    normalized_regret: float
    expected_recovery_absolute_error: float
    expected_value_absolute_error: float
    outcome_reason: str

    @property
    def expected_vs_actual_error(self) -> float:
        """Compatibility alias for the former recovery-only error name."""
        return self.expected_recovery_absolute_error


@dataclass(frozen=True)
class StrategyMetrics:
    strategy_name: str
    total_cases: int
    recovered_cases: int
    case_recovery_rate: float
    attempt_rate: float
    attempt_recovery_rate: float
    total_attempted_amount: float
    total_recovered_amount: float
    total_action_cost: float
    total_net_value: float
    average_net_value_per_case: float
    average_expected_value: float
    policy_violations: int
    policy_compliance_rate: float
    action_distribution: dict[str, int]
    regret_rate: float
    average_regret: float
    total_regret: float
    average_normalized_regret: float
    expected_recovery_absolute_error: float
    expected_value_absolute_error: float

    @property
    def recovery_rate(self) -> float:
        """Compatibility alias for callers using the old metric name."""
        return self.case_recovery_rate

    @property
    def expected_vs_actual_error(self) -> float:
        """Compatibility alias for the former recovery-only error name."""
        return self.expected_recovery_absolute_error


def aggregate_metrics(strategy_name: str, results: list[PerCaseResult]) -> StrategyMetrics:
    total_cases = len(results)
    recovered_cases = sum(1 for result in results if result.recovered)
    attempted_cases = sum(1 for result in results if result.attempted_amount > 0)
    total_net_value = sum(result.realized_net_value for result in results)
    total_regret = sum(max(0.0, result.regret) for result in results)
    return StrategyMetrics(
        strategy_name=strategy_name,
        total_cases=total_cases,
        recovered_cases=recovered_cases,
        case_recovery_rate=recovered_cases / total_cases if total_cases else 0.0,
        attempt_rate=attempted_cases / total_cases if total_cases else 0.0,
        attempt_recovery_rate=recovered_cases / attempted_cases if attempted_cases else 0.0,
        total_attempted_amount=round(sum(result.attempted_amount for result in results), 2),
        total_recovered_amount=round(sum(result.recovered_amount for result in results), 2),
        total_action_cost=round(sum(result.action_cost for result in results), 2),
        total_net_value=round(total_net_value, 2),
        average_net_value_per_case=round(total_net_value / total_cases, 2) if total_cases else 0.0,
        average_expected_value=round(sum(result.expected_value for result in results) / total_cases, 2) if total_cases else 0.0,
        policy_violations=sum(1 for result in results if not result.allowed),
        policy_compliance_rate=(sum(1 for result in results if result.allowed) / total_cases) if total_cases else 0.0,
        action_distribution=dict(Counter(result.selected_action for result in results)),
        regret_rate=sum(1 for result in results if result.regret > 0) / total_cases if total_cases else 0.0,
        average_regret=round(total_regret / total_cases, 2) if total_cases else 0.0,
        total_regret=round(total_regret, 2),
        average_normalized_regret=round(sum(result.normalized_regret for result in results) / total_cases, 6) if total_cases else 0.0,
        expected_recovery_absolute_error=round(sum(result.expected_recovery_absolute_error for result in results) / total_cases, 2) if total_cases else 0.0,
        expected_value_absolute_error=round(sum(result.expected_value_absolute_error for result in results) / total_cases, 2) if total_cases else 0.0,
    )
