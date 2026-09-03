from __future__ import annotations

from pydantic import BaseModel


class EvaluationSummaryResponse(BaseModel):
    dataset_size: int
    seeds: list[int]
    strategies: list[str]
    best_baseline: str | None
    reclaim_recovery_rate: float
    best_baseline_recovery_rate: float
    incremental_recovered_amount: float
    incremental_net_value: float
    reclaim_policy_compliance_rate: float
    reclaim_average_regret: float
    reclaim_regret_rate: float


class StrategyEvaluationResponse(BaseModel):
    strategy_name: str
    total_cases: int
    case_recovery_rate: float
    attempt_rate: float
    attempt_recovery_rate: float
    total_recovered_amount: float
    total_action_cost: float
    total_net_value: float
    average_net_value_per_case: float
    policy_violations: int
    policy_compliance_rate: float
    average_regret: float
    regret_rate: float
    average_normalized_regret: float
    expected_recovery_absolute_error: float
    expected_value_absolute_error: float
    action_distribution: dict[str, int]


class MultiSeedStrategyResponse(BaseModel):
    strategy_name: str
    mean_case_recovery_rate: float
    mean_recovered_amount: float
    mean_net_value: float
    mean_policy_violations: float
    mean_regret: float
    stddev_net_value: float
    minimum_net_value: float
    maximum_net_value: float


class ScenarioEvaluationResponse(BaseModel):
    scenario: str
    strategy: str
    total_cases: int
    case_recovery_rate: float
    total_recovered_amount: float
    total_net_value: float
    policy_violations: int
    average_regret: float


class PerCaseEvaluationResponse(BaseModel):
    case_id: str
    strategy: str
    scenario_labels: list[str]
    selected_action: str
    allowed: bool
    expected_recovery: float
    expected_value: float
    recovered: bool
    recovered_amount: float
    action_cost: float
    realized_net_value: float
    regret: float
    outcome_reason: str


class EvaluationErrorResponse(BaseModel):
    error: str
    message: str
    detail: str | None = None
