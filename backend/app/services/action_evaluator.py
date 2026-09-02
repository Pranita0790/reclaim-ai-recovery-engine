from __future__ import annotations

from app.core.constants import ACTION_COSTS
from app.ml.model_predictor import RecoveryModelPredictor
from app.models.case import RecoveryCase
from app.models.decision import (
    ActionScore,
    RecoveryAction,
)
from app.services.baseline_estimator import BaselineEstimator
from app.services.policy_engine import PolicyEngine


class ActionEvaluator:
    """
    Evaluate recovery actions using:

    - Deterministic baseline business signals
    - ML recovery probability
    - Policy constraints
    - Expected business value
    """

    def __init__(
        self,
        baseline_estimator: BaselineEstimator | None = None,
        policy_engine: PolicyEngine | None = None,
        model_predictor: RecoveryModelPredictor | None = None,
    ) -> None:
        self.baseline_estimator = (
            baseline_estimator or BaselineEstimator()
        )

        self.policy_engine = (
            policy_engine or PolicyEngine()
        )

        self.model_predictor = (
            model_predictor or RecoveryModelPredictor()
        )

    @staticmethod
    def _combine_probabilities(
        baseline_probability: float,
        ml_probability: float,
    ) -> float:
        """
        Combine deterministic business probability with
        ML model probability.

        Baseline signals have 60% weight.
        ML prediction has 40% weight.
        """

        combined_probability = (
            (baseline_probability * 0.60)
            + (ml_probability * 0.40)
        )

        return max(
            0.0,
            min(combined_probability, 1.0),
        )

    def evaluate(
        self,
        case: RecoveryCase,
        action: RecoveryAction,
    ) -> ActionScore:
        """Evaluate one possible recovery action."""

        # --------------------------------------------------
        # POLICY CHECK
        # --------------------------------------------------

        is_allowed, policy_reason = (
            self.policy_engine.evaluate(
                case,
                action,
            )
        )

        # --------------------------------------------------
        # BASELINE PROBABILITY
        # --------------------------------------------------

        baseline_probability = (
            self.baseline_estimator.estimate(
                case,
                action,
            )
        )

        # --------------------------------------------------
        # ML PROBABILITY
        # --------------------------------------------------

        if action is RecoveryAction.DO_NOTHING:
            success_probability = 0.0
        else:
            ml_probability = (
                self.model_predictor
                .predict_recovery_probability(case)
            )

            success_probability = (
                self._combine_probabilities(
                    baseline_probability,
                    ml_probability,
                )
            )

        # --------------------------------------------------
        # ECONOMICS
        # --------------------------------------------------

        action_cost = ACTION_COSTS[action]

        expected_recovery = (
            case.amount * success_probability
        )

        expected_value = (
            expected_recovery - action_cost
        )

        # Blocked actions should never produce
        # positive business value.
        if not is_allowed:
            expected_value = 0.0

        return ActionScore(
            action=action,
            success_probability=round(
                success_probability,
                4,
            ),
            expected_recovery=round(
                expected_recovery,
                2,
            ),
            action_cost=round(
                action_cost,
                2,
            ),
            expected_value=round(
                expected_value,
                2,
            ),
            is_allowed=is_allowed,
            reason=policy_reason,
        )

    def evaluate_all(
        self,
        case: RecoveryCase,
    ) -> list[ActionScore]:
        """Evaluate every available recovery action."""

        return [
            self.evaluate(case, action)
            for action in RecoveryAction
        ]