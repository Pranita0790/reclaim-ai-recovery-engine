from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.models.case import RecoveryCase
from app.models.decision import RecoveryAction
from app.services.action_evaluator import ActionEvaluator
from app.services.decision_engine import DecisionEngine
from app.services.policy_engine import PolicyEngine


@dataclass(frozen=True)
class StrategyDecision:
    strategy_name: str
    selected_action: RecoveryAction
    allowed: bool
    expected_recovery: float
    expected_value: float
    success_probability: float
    reason: str


class RecoveryStrategy(Protocol):
    name: str

    def decide(self, case: RecoveryCase) -> StrategyDecision:
        ...


class ReclaimHybridStrategy:
    name = "RECLAIM Hybrid"

    def __init__(self, decision_engine: DecisionEngine | None = None) -> None:
        self.decision_engine = decision_engine or DecisionEngine()

    def decide(self, case: RecoveryCase) -> StrategyDecision:
        decision = self.decision_engine.decide(case)
        selected = next(
            (item for item in decision.evaluated_actions if item.action is decision.recommended_action),
            None,
        )
        is_do_nothing = decision.recommended_action is RecoveryAction.DO_NOTHING
        return StrategyDecision(
            strategy_name=self.name,
            selected_action=decision.recommended_action,
            allowed=(selected.is_allowed if selected is not None else False) or is_do_nothing,
            expected_recovery=selected.expected_recovery if selected is not None else decision.expected_recovery,
            expected_value=selected.expected_value if selected is not None else decision.expected_value,
            success_probability=selected.success_probability if selected is not None else decision.confidence,
            reason=selected.reason if selected is not None else decision.explanation,
        )


class FixedActionStrategy:
    action: RecoveryAction
    name: str

    def __init__(self, action: RecoveryAction, name: str, action_evaluator: ActionEvaluator | None = None) -> None:
        self.action = action
        self.name = name
        self.action_evaluator = action_evaluator or ActionEvaluator()
        self.policy_engine = PolicyEngine()

    def decide(self, case: RecoveryCase) -> StrategyDecision:
        score = self.action_evaluator.evaluate(case, self.action)
        allowed, reason = self.policy_engine.evaluate(case, self.action)
        if self.action is RecoveryAction.DO_NOTHING:
            allowed, reason = True, "No action is always allowed."
        return StrategyDecision(
            strategy_name=self.name,
            selected_action=self.action,
            allowed=allowed,
            expected_recovery=score.expected_recovery,
            expected_value=score.expected_value if allowed else 0.0,
            success_probability=score.success_probability,
            reason=reason,
        )


class AlwaysRetryStrategy(FixedActionStrategy):
    def __init__(self, action_evaluator: ActionEvaluator | None = None) -> None:
        super().__init__(RecoveryAction.RETRY_PAYMENT, "Always Retry", action_evaluator)


class AlwaysContactStrategy(FixedActionStrategy):
    def __init__(self, action_evaluator: ActionEvaluator | None = None) -> None:
        super().__init__(RecoveryAction.CONTACT_CUSTOMER, "Always Contact", action_evaluator)


class AlwaysEscalateStrategy(FixedActionStrategy):
    def __init__(self, action_evaluator: ActionEvaluator | None = None) -> None:
        super().__init__(RecoveryAction.ESCALATE, "Always Escalate", action_evaluator)


class DoNothingStrategy(FixedActionStrategy):
    def __init__(self, action_evaluator: ActionEvaluator | None = None) -> None:
        super().__init__(RecoveryAction.DO_NOTHING, "Do Nothing", action_evaluator)


def default_strategies() -> list[RecoveryStrategy]:
    return [
        ReclaimHybridStrategy(),
        AlwaysRetryStrategy(),
        AlwaysContactStrategy(),
        AlwaysEscalateStrategy(),
        DoNothingStrategy(),
    ]
