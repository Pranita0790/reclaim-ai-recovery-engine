from __future__ import annotations

from app.core.constants import (
    HIGH_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    MIN_POSITIVE_EXPECTED_VALUE,
)
from app.ml.model_predictor import RecoveryModelPredictor
from app.models.case import RecoveryCase
from app.models.decision import (
    DecisionStatus,
    RecoveryAction,
    RecoveryDecision,
)
from app.services.action_evaluator import ActionEvaluator


class DecisionEngine:
    """
    Select the best recovery action using a hybrid
    rules + ML decision-making approach.
    """

    def __init__(
        self,
        action_evaluator: ActionEvaluator | None = None,
        model_predictor: RecoveryModelPredictor | None = None,
    ) -> None:
        self.action_evaluator = (
            action_evaluator or ActionEvaluator()
        )

        self.model_predictor = (
            model_predictor or RecoveryModelPredictor()
        )

    def decide(
        self,
        case: RecoveryCase,
    ) -> RecoveryDecision:
        """
        Evaluate all recovery actions and select the
        best allowed action using policy, economics,
        and ML recovery probability.
        """

        # --------------------------------------------------
        # ML PREDICTION
        # --------------------------------------------------

        ml_recovery_probability = (
            self.model_predictor.predict_recovery_probability(
                case
            )
        )

        # --------------------------------------------------
        # ACTION EVALUATION
        # --------------------------------------------------

        evaluated_actions = (
            self.action_evaluator.evaluate_all(case)
        )

        # Keep only actions allowed by the policy engine.
        allowed_actions = [
            action
            for action in evaluated_actions
            if action.is_allowed
        ]

        # --------------------------------------------------
        # ALL ACTIONS BLOCKED
        # --------------------------------------------------

        if not allowed_actions:
            return RecoveryDecision(
                case_id=case.case_id,
                recommended_action=(
                    RecoveryAction.DO_NOTHING
                ),
                status=DecisionStatus.BLOCKED_BY_POLICY,
                confidence=0.0,
                expected_recovery=0.0,
                expected_value=0.0,
                explanation=(
                    "No recovery actions are currently "
                    "allowed by policy."
                ),
                evaluated_actions=evaluated_actions,
                policy_checks=[
                    "All recovery actions were blocked "
                    "by policy."
                ],
                ml_recovery_probability=(
                    ml_recovery_probability
                ),
                decision_source=(
                    "HYBRID_RULES_AND_ML"
                ),
            )

        # --------------------------------------------------
        # SELECT BEST ACTION
        # --------------------------------------------------

        best_action = max(
            allowed_actions,
            key=lambda action: action.expected_value,
        )

        # --------------------------------------------------
        # NO POSITIVE BUSINESS VALUE
        # --------------------------------------------------

        if (
            best_action.expected_value
            <= MIN_POSITIVE_EXPECTED_VALUE
        ):
            return RecoveryDecision(
                case_id=case.case_id,
                recommended_action=(
                    RecoveryAction.DO_NOTHING
                ),
                status=DecisionStatus.REJECTED,
                confidence=0.0,
                expected_recovery=0.0,
                expected_value=0.0,
                explanation=(
                    "No allowed recovery action has "
                    "a positive expected value. "
                    f"The ML model predicted a "
                    f"{ml_recovery_probability:.2%} "
                    "overall recovery probability."
                ),
                evaluated_actions=evaluated_actions,
                policy_checks=[
                    action.reason
                    for action in evaluated_actions
                ],
                ml_recovery_probability=(
                    ml_recovery_probability
                ),
                decision_source=(
                    "HYBRID_RULES_AND_ML"
                ),
            )

        # --------------------------------------------------
        # CONFIDENCE LEVEL
        # --------------------------------------------------

        confidence = (
            best_action.success_probability
        )

        if confidence >= HIGH_CONFIDENCE_THRESHOLD:
            confidence_label = "high"

        elif confidence >= MEDIUM_CONFIDENCE_THRESHOLD:
            confidence_label = "medium"

        else:
            confidence_label = "low"

        # --------------------------------------------------
        # APPROVED DECISION
        # --------------------------------------------------

        return RecoveryDecision(
            case_id=case.case_id,
            recommended_action=best_action.action,
            status=DecisionStatus.APPROVED,
            confidence=confidence,
            expected_recovery=(
                best_action.expected_recovery
            ),
            expected_value=best_action.expected_value,
            explanation=(
                f"Recommended {best_action.action.value} "
                f"because it has the highest expected "
                f"value among all allowed actions. "
                f"Decision confidence is "
                f"{confidence_label}. "
                f"The ML model predicted a "
                f"{ml_recovery_probability:.2%} "
                f"overall recovery probability."
            ),
            evaluated_actions=evaluated_actions,
            policy_checks=[
                action.reason
                for action in evaluated_actions
            ],
            ml_recovery_probability=(
                ml_recovery_probability
            ),
            decision_source=(
                "HYBRID_RULES_AND_ML"
            ),
        )