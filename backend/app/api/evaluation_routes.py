from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.evaluation_schemas import (
    EvaluationSummaryResponse,
    MultiSeedStrategyResponse,
    PerCaseEvaluationResponse,
    ScenarioEvaluationResponse,
    StrategyEvaluationResponse,
)
from app.api.replay_schemas import (
    ReplayCandidateResponse,
    ReplayCaseResponse,
    ReplayDecisionResponse,
    ReplayResponse,
)
from app.evaluation.dataset_loader import DatasetValidationError
from app.evaluation.metrics import PerCaseResult, StrategyMetrics
from app.evaluation.runner import EvaluationResult, MultiSeedEvaluationResult
from app.evaluation.replay import ReplayResult
from app.services.evaluation_service import EvaluationService


router = APIRouter(prefix="/evaluation", tags=["Evaluation"])
evaluation_service = EvaluationService()


def _load_results() -> tuple[EvaluationResult, MultiSeedEvaluationResult]:
    try:
        return evaluation_service.results()
    except DatasetValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Evaluation failed: {error}") from error


def _strategy_response(metrics: StrategyMetrics) -> StrategyEvaluationResponse:
    return StrategyEvaluationResponse(
        strategy_name=metrics.strategy_name,
        total_cases=metrics.total_cases,
        case_recovery_rate=metrics.case_recovery_rate,
        attempt_rate=metrics.attempt_rate,
        attempt_recovery_rate=metrics.attempt_recovery_rate,
        total_recovered_amount=metrics.total_recovered_amount,
        total_action_cost=metrics.total_action_cost,
        total_net_value=metrics.total_net_value,
        average_net_value_per_case=metrics.average_net_value_per_case,
        policy_violations=metrics.policy_violations,
        policy_compliance_rate=metrics.policy_compliance_rate,
        average_regret=metrics.average_regret,
        regret_rate=metrics.regret_rate,
        average_normalized_regret=metrics.average_normalized_regret,
        expected_recovery_absolute_error=metrics.expected_recovery_absolute_error,
        expected_value_absolute_error=metrics.expected_value_absolute_error,
        action_distribution=metrics.action_distribution,
    )


def _case_response(result: PerCaseResult) -> PerCaseEvaluationResponse:
    return PerCaseEvaluationResponse(
        case_id=result.case_id,
        strategy=result.strategy,
        scenario_labels=list(result.scenarios),
        selected_action=result.selected_action,
        allowed=result.allowed,
        expected_recovery=result.expected_recovery,
        expected_value=result.expected_value,
        recovered=result.recovered,
        recovered_amount=result.recovered_amount,
        action_cost=result.action_cost,
        realized_net_value=result.realized_net_value,
        regret=result.regret,
        outcome_reason=result.outcome_reason,
    )


def _replay_response(result: ReplayResult) -> ReplayResponse:
    return ReplayResponse(
        case=ReplayCaseResponse(
            case_id=result.case.case_id,
            customer_id=result.case.customer_id,
            amount=result.case.amount,
            currency=result.case.currency,
            payment_status=result.case.payment_status,
            failure_reason=result.case.failure_reason,
            failure_count=result.case.failure_count,
            customer_attempt_count=result.case.customer_attempt_count,
            days_since_failure=result.case.days_since_failure,
            is_customer_active=result.case.is_customer_active,
            has_valid_payment_method=result.case.has_valid_payment_method,
            scenario_labels=list(result.case.scenario_labels),
        ),
        strategy=result.strategy,
        seed=result.seed,
        decision=ReplayDecisionResponse(
            selected_action=result.decision.selected_action.value,
            decision_status=result.decision.decision_status,
            confidence=result.decision.confidence,
            ml_recovery_probability=result.decision.ml_recovery_probability,
            decision_source=result.decision.decision_source,
            explanation=result.decision.explanation,
        ),
        candidates=[
            ReplayCandidateResponse(
                action=candidate.action.value,
                is_allowed=candidate.is_allowed,
                policy_reason=candidate.policy_reason,
                success_probability=candidate.success_probability,
                expected_recovery=candidate.expected_recovery,
                expected_value=candidate.expected_value,
                action_cost=candidate.action_cost,
                recovered=candidate.recovered,
                recovered_amount=candidate.recovered_amount,
                realized_net_value=candidate.realized_net_value,
                outcome_reason=candidate.outcome_reason,
                is_selected=candidate.is_selected,
            )
            for candidate in result.candidates
        ],
        regret=result.regret,
        best_realized_action=result.best_realized_action.value,
        best_realized_net_value=result.best_realized_net_value,
    )


@router.get("/summary", response_model=EvaluationSummaryResponse)
def get_evaluation_summary() -> EvaluationSummaryResponse:
    single, multi = _load_results()
    hybrid_multi = multi.strategy_results.get("RECLAIM Hybrid")
    baseline_multi = [metrics for name, metrics in multi.strategy_results.items() if name != "RECLAIM Hybrid"]
    best_baseline = max(baseline_multi, key=lambda metrics: metrics.mean_net_value) if baseline_multi else None
    hybrid_seed_metrics = [result.strategy_results["RECLAIM Hybrid"] for result in multi.seed_results]
    return EvaluationSummaryResponse(
        dataset_size=multi.dataset_size,
        seeds=multi.seeds,
        strategies=multi.strategies,
        best_baseline=best_baseline.strategy_name if best_baseline else None,
        reclaim_recovery_rate=hybrid_multi.mean_case_recovery_rate if hybrid_multi else 0.0,
        best_baseline_recovery_rate=best_baseline.mean_case_recovery_rate if best_baseline else 0.0,
        incremental_recovered_amount=round((hybrid_multi.mean_recovered_amount - best_baseline.mean_recovered_amount) if hybrid_multi and best_baseline else 0.0, 2),
        incremental_net_value=round((hybrid_multi.mean_net_value - best_baseline.mean_net_value) if hybrid_multi and best_baseline else 0.0, 2),
        reclaim_policy_compliance_rate=sum(metrics.policy_compliance_rate for metrics in hybrid_seed_metrics) / len(hybrid_seed_metrics) if hybrid_seed_metrics else 0.0,
        reclaim_average_regret=hybrid_multi.mean_regret if hybrid_multi else 0.0,
        reclaim_regret_rate=sum(metrics.regret_rate for metrics in hybrid_seed_metrics) / len(hybrid_seed_metrics) if hybrid_seed_metrics else 0.0,
    )


@router.get("/replay/{case_id}", response_model=ReplayResponse)
def get_evaluation_replay(
    case_id: str,
    seed: int = Query(default=42, ge=0),
) -> ReplayResponse:
    try:
        return _replay_response(evaluation_service.get_replay(case_id, seed))
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No evaluation case found for '{case_id}'.") from error
    except DatasetValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Evaluation failed: {error}") from error


@router.get("/strategies", response_model=list[StrategyEvaluationResponse])
def get_strategy_results() -> list[StrategyEvaluationResponse]:
    single, _ = _load_results()
    return [_strategy_response(metrics) for metrics in single.strategy_results.values()]


@router.get("/multiseed", response_model=list[MultiSeedStrategyResponse])
def get_multiseed_results() -> list[MultiSeedStrategyResponse]:
    _, multi = _load_results()
    return [MultiSeedStrategyResponse(**metrics.__dict__) for metrics in multi.strategy_results.values()]


@router.get("/scenarios", response_model=list[ScenarioEvaluationResponse])
def get_scenario_results(strategy: str | None = None) -> list[ScenarioEvaluationResponse]:
    single, _ = _load_results()
    responses: list[ScenarioEvaluationResponse] = []
    for scenario, strategy_metrics in sorted(single.scenario_results.items()):
        for strategy_name, metrics in strategy_metrics.items():
            if strategy and strategy_name != strategy:
                continue
            responses.append(ScenarioEvaluationResponse(
                scenario=scenario,
                strategy=strategy_name,
                total_cases=metrics.total_cases,
                case_recovery_rate=metrics.case_recovery_rate,
                total_recovered_amount=metrics.total_recovered_amount,
                total_net_value=metrics.total_net_value,
                policy_violations=metrics.policy_violations,
                average_regret=metrics.average_regret,
            ))
    return responses


@router.get("/cases", response_model=list[PerCaseEvaluationResponse])
def get_case_results(
    strategy: str | None = None,
    scenario: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[PerCaseEvaluationResponse]:
    single, _ = _load_results()
    filtered = [
        result for result in single.per_case_results
        if (strategy is None or result.strategy == strategy)
        and (scenario is None or scenario in result.scenarios)
    ]
    return [_case_response(result) for result in filtered[:limit]]
