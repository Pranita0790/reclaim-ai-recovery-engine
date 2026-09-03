from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean, pstdev
from typing import Any, Sequence

from app.evaluation.dataset_loader import EvaluationCase
from app.evaluation.metrics import PerCaseResult, StrategyMetrics, aggregate_metrics
from app.evaluation.outcome_simulator import OutcomeSimulator
from app.evaluation.strategies import RecoveryStrategy, StrategyDecision, default_strategies
from app.models.case import RecoveryCase
from app.models.decision import RecoveryAction
from app.services.policy_engine import PolicyEngine


@dataclass(frozen=True)
class MultiSeedStrategyMetrics:
    strategy_name: str
    seeds: int
    mean_case_recovery_rate: float
    mean_recovered_amount: float
    mean_net_value: float
    mean_policy_violations: float
    mean_regret: float
    stddev_net_value: float
    minimum_net_value: float
    maximum_net_value: float


@dataclass(frozen=True)
class EvaluationResult:
    dataset_size: int
    seed: int
    strategies: list[str]
    strategy_results: dict[str, StrategyMetrics]
    per_case_results: list[PerCaseResult]
    scenario_results: dict[str, dict[str, StrategyMetrics]]
    best_baseline_strategy: str | None
    incremental_recovered_amount: float
    incremental_net_value: float
    incremental_recovery_rate: float
    incremental_attempt_recovery_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_size": self.dataset_size,
            "seed": self.seed,
            "strategies": self.strategies,
            "strategy_results": {name: asdict(metrics) for name, metrics in self.strategy_results.items()},
            "per_case_results": [asdict(result) for result in self.per_case_results],
            "scenario_results": {
                scenario: {name: asdict(metrics) for name, metrics in metrics_by_strategy.items()}
                for scenario, metrics_by_strategy in self.scenario_results.items()
            },
            "best_baseline_strategy": self.best_baseline_strategy,
            "incremental_recovered_amount": self.incremental_recovered_amount,
            "incremental_net_value": self.incremental_net_value,
            "incremental_recovery_rate": self.incremental_recovery_rate,
            "incremental_attempt_recovery_rate": self.incremental_attempt_recovery_rate,
        }


@dataclass(frozen=True)
class MultiSeedEvaluationResult:
    dataset_size: int
    seeds: list[int]
    strategies: list[str]
    strategy_results: dict[str, MultiSeedStrategyMetrics]
    seed_results: list[EvaluationResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_size": self.dataset_size,
            "seeds": self.seeds,
            "strategies": self.strategies,
            "strategy_results": {name: asdict(metrics) for name, metrics in self.strategy_results.items()},
            "seed_results": [result.to_dict() for result in self.seed_results],
        }


class EvaluationRunner:
    def __init__(self, seed: int = 42, strategies: list[RecoveryStrategy] | None = None) -> None:
        self.seed = seed
        self.strategies = strategies or default_strategies()
        self.policy_engine = PolicyEngine()

    @staticmethod
    def _unwrap(case: EvaluationCase | RecoveryCase) -> tuple[RecoveryCase, tuple[str, ...]]:
        if isinstance(case, EvaluationCase):
            return case.case, case.scenarios
        return case, ("MIXED",)

    def _available_outcomes(self, case: RecoveryCase, simulator: OutcomeSimulator):
        outcomes = {}
        valid_actions: set[RecoveryAction] = set()
        for action in RecoveryAction:
            allowed, _ = self.policy_engine.evaluate(case, action)
            if action is RecoveryAction.DO_NOTHING:
                allowed = True
            if allowed:
                valid_actions.add(action)
            outcomes[action] = simulator.simulate(case, action, allowed)
        return outcomes, valid_actions

    def _case_result(self, case: RecoveryCase, scenarios: tuple[str, ...], strategy: RecoveryStrategy, decision: StrategyDecision, outcomes, valid_actions: set[RecoveryAction]) -> PerCaseResult:
        selected_outcome = outcomes[decision.selected_action]
        best_valid_net_value = max((outcomes[action].net_value for action in valid_actions), default=selected_outcome.net_value)
        regret = max(0.0, best_valid_net_value - selected_outcome.net_value)
        expected_recovery_error = abs(decision.expected_recovery - selected_outcome.recovered_amount)
        expected_value_error = abs(decision.expected_value - selected_outcome.net_value)
        attempted_amount = case.amount if decision.allowed and decision.selected_action is not RecoveryAction.DO_NOTHING else 0.0
        return PerCaseResult(
            case_id=case.case_id,
            strategy=strategy.name,
            scenarios=scenarios,
            attempted_amount=attempted_amount,
            case_amount=case.amount,
            selected_action=decision.selected_action.value,
            allowed=decision.allowed,
            expected_recovery=decision.expected_recovery,
            expected_value=decision.expected_value,
            recovered=selected_outcome.recovered,
            recovered_amount=selected_outcome.recovered_amount,
            action_cost=selected_outcome.action_cost,
            realized_net_value=selected_outcome.net_value,
            regret=regret,
            normalized_regret=regret / case.amount if case.amount > 0 else 0.0,
            expected_recovery_absolute_error=expected_recovery_error,
            expected_value_absolute_error=expected_value_error,
            outcome_reason=selected_outcome.outcome_reason if decision.allowed else decision.reason,
        )

    def run(self, cases: Sequence[EvaluationCase | RecoveryCase]) -> EvaluationResult:
        all_results: list[PerCaseResult] = []
        metrics: dict[str, StrategyMetrics] = {}
        scenario_metrics: dict[str, dict[str, StrategyMetrics]] = {}
        for strategy in self.strategies:
            simulator = OutcomeSimulator(self.seed)
            strategy_results: list[PerCaseResult] = []
            for raw_case in cases:
                case, scenarios = self._unwrap(raw_case)
                decision = strategy.decide(case)
                outcomes, valid_actions = self._available_outcomes(case, simulator)
                strategy_results.append(self._case_result(case, scenarios, strategy, decision, outcomes, valid_actions))
            all_results.extend(strategy_results)
            metrics[strategy.name] = aggregate_metrics(strategy.name, strategy_results)
            for scenario in sorted({scenario for result in strategy_results for scenario in result.scenarios}):
                grouped = [result for result in strategy_results if scenario in result.scenarios]
                scenario_metrics.setdefault(scenario, {})[strategy.name] = aggregate_metrics(strategy.name, grouped)

        hybrid = metrics.get("RECLAIM Hybrid")
        baselines = [item for name, item in metrics.items() if name != "RECLAIM Hybrid"]
        best_baseline = max(baselines, key=lambda item: item.total_net_value) if baselines else None
        return EvaluationResult(
            dataset_size=len(cases), seed=self.seed, strategies=[strategy.name for strategy in self.strategies],
            strategy_results=metrics, per_case_results=all_results, scenario_results=scenario_metrics,
            best_baseline_strategy=best_baseline.strategy_name if best_baseline else None,
            incremental_recovered_amount=round((hybrid.total_recovered_amount - best_baseline.total_recovered_amount) if hybrid and best_baseline else 0.0, 2),
            incremental_net_value=round((hybrid.total_net_value - best_baseline.total_net_value) if hybrid and best_baseline else 0.0, 2),
            incremental_recovery_rate=(hybrid.case_recovery_rate - best_baseline.case_recovery_rate) if hybrid and best_baseline else 0.0,
            incremental_attempt_recovery_rate=(hybrid.attempt_recovery_rate - best_baseline.attempt_recovery_rate) if hybrid and best_baseline else 0.0,
        )

    def run_many(self, cases: Sequence[EvaluationCase | RecoveryCase], seeds: Sequence[int]) -> MultiSeedEvaluationResult:
        if not seeds:
            raise ValueError("At least one seed is required.")
        results = [EvaluationRunner(seed=seed, strategies=self.strategies).run(cases) for seed in seeds]
        names = [strategy.name for strategy in self.strategies]
        aggregated: dict[str, MultiSeedStrategyMetrics] = {}
        for name in names:
            values = [result.strategy_results[name] for result in results]
            net_values = [value.total_net_value for value in values]
            aggregated[name] = MultiSeedStrategyMetrics(
                strategy_name=name,
                seeds=len(results),
                mean_case_recovery_rate=mean(value.case_recovery_rate for value in values),
                mean_recovered_amount=mean(value.total_recovered_amount for value in values),
                mean_net_value=mean(net_values),
                mean_policy_violations=mean(value.policy_violations for value in values),
                mean_regret=mean(value.average_regret for value in values),
                stddev_net_value=pstdev(net_values) if len(net_values) > 1 else 0.0,
                minimum_net_value=min(net_values),
                maximum_net_value=max(net_values),
            )
        return MultiSeedEvaluationResult(len(cases), list(seeds), names, aggregated, results)
