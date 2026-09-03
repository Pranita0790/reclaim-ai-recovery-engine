from __future__ import annotations

from pathlib import Path
from threading import Lock

from app.evaluation.dataset_loader import EvaluationCase, DatasetValidationError, load_cases
from app.evaluation.outcome_simulator import OutcomeSimulator
from app.evaluation.replay import (
    ReplayCandidate,
    ReplayCase,
    ReplayDecision,
    ReplayResult,
)
from app.evaluation.runner import EvaluationResult, EvaluationRunner, MultiSeedEvaluationResult
from app.models.decision import RecoveryAction
from app.services.action_evaluator import ActionEvaluator
from app.services.decision_engine import DecisionEngine
from app.services.policy_engine import PolicyEngine


DEFAULT_SEEDS = (42, 43, 44, 45, 46)


class EvaluationService:
    """Read-only access to deterministic results from the evaluation engine."""

    def __init__(self, dataset_path: str | Path | None = None) -> None:
        self.dataset_path = Path(dataset_path) if dataset_path else Path(__file__).resolve().parents[2] / "data" / "cases.csv"
        self._lock = Lock()
        self._cached_signature: tuple[int, tuple[int, ...]] | None = None
        self._cached_single: EvaluationResult | None = None
        self._cached_multi: MultiSeedEvaluationResult | None = None

    def _ensure_loaded(self) -> tuple[EvaluationResult, MultiSeedEvaluationResult]:
        if not self.dataset_path.exists():
            raise DatasetValidationError(f"Evaluation dataset does not exist: {self.dataset_path}")
        signature = (self.dataset_path.stat().st_mtime_ns, DEFAULT_SEEDS)
        if self._cached_signature == signature and self._cached_single and self._cached_multi:
            return self._cached_single, self._cached_multi
        with self._lock:
            if self._cached_signature == signature and self._cached_single and self._cached_multi:
                return self._cached_single, self._cached_multi
            cases = load_cases(self.dataset_path)
            runner = EvaluationRunner(seed=DEFAULT_SEEDS[0])
            multi = runner.run_many(cases, DEFAULT_SEEDS)
            single = multi.seed_results[0]
            self._cached_signature = signature
            self._cached_single = single
            self._cached_multi = multi
            return single, multi

    def results(self) -> tuple[EvaluationResult, MultiSeedEvaluationResult]:
        return self._ensure_loaded()

    def cases(self) -> list[EvaluationCase]:
        return load_cases(self.dataset_path)

    def get_replay(self, case_id: str, seed: int = 42) -> ReplayResult:
        """Compose a deterministic replay from the existing evaluation primitives."""

        evaluation_case = next(
            (item for item in self.cases() if item.case.case_id == case_id),
            None,
        )
        if evaluation_case is None:
            raise KeyError(case_id)

        case = evaluation_case.case
        decision = DecisionEngine().decide(case)
        action_evaluator = ActionEvaluator()
        policy_engine = PolicyEngine()
        simulator = OutcomeSimulator(seed)
        candidates: list[ReplayCandidate] = []

        for action in RecoveryAction:
            score = action_evaluator.evaluate(case, action)
            is_allowed, policy_reason = policy_engine.evaluate(case, action)
            if action is RecoveryAction.DO_NOTHING:
                is_allowed = True
                policy_reason = "No action is always allowed."
            outcome = simulator.simulate(case, action, is_allowed)
            candidates.append(
                ReplayCandidate(
                    action=action,
                    is_allowed=is_allowed,
                    policy_reason=policy_reason,
                    success_probability=score.success_probability,
                    expected_recovery=score.expected_recovery,
                    expected_value=score.expected_value if is_allowed else 0.0,
                    action_cost=outcome.action_cost,
                    recovered=outcome.recovered,
                    recovered_amount=outcome.recovered_amount,
                    realized_net_value=outcome.net_value,
                    outcome_reason=outcome.outcome_reason,
                    is_selected=action is decision.recommended_action,
                )
            )

        valid_candidates = [candidate for candidate in candidates if candidate.is_allowed]
        best_candidate = max(
            valid_candidates,
            key=lambda candidate: candidate.realized_net_value,
            default=ReplayCandidate(
                action=RecoveryAction.DO_NOTHING,
                is_allowed=True,
                policy_reason="No action is always allowed.",
                success_probability=0.0,
                expected_recovery=0.0,
                expected_value=0.0,
                action_cost=0.0,
                recovered=False,
                recovered_amount=0.0,
                realized_net_value=0.0,
                outcome_reason="No recovery action attempted.",
                is_selected=False,
            ),
        )
        selected_candidate = next(
            candidate for candidate in candidates if candidate.is_selected
        )

        return ReplayResult(
            case=ReplayCase.from_case(case, evaluation_case.scenarios),
            strategy="RECLAIM Hybrid",
            seed=seed,
            decision=ReplayDecision(
                selected_action=decision.recommended_action,
                decision_status=decision.status.value,
                confidence=decision.confidence,
                ml_recovery_probability=decision.ml_recovery_probability or 0.0,
                decision_source=decision.decision_source,
                explanation=decision.explanation,
            ),
            candidates=tuple(candidates),
            regret=max(0.0, best_candidate.realized_net_value - selected_candidate.realized_net_value),
            best_realized_action=best_candidate.action,
            best_realized_net_value=best_candidate.realized_net_value,
        )
