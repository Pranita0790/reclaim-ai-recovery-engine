from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from app.core.constants import ACTION_COSTS, BASE_SUCCESS_PROBABILITIES
from app.models.case import FailureReason, RecoveryCase
from app.models.decision import RecoveryAction


@dataclass(frozen=True)
class SimulatedOutcome:
    recovered: bool
    recovered_amount: float
    action_cost: float
    net_value: float
    outcome_reason: str
    probability: float


class OutcomeSimulator:
    """Generate independent, reproducible realized outcomes for evaluation."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def _randomizer(self, case: RecoveryCase, action: RecoveryAction) -> random.Random:
        key = f"{self.seed}:{case.case_id}:{action.value}".encode("utf-8")
        derived_seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
        return random.Random(derived_seed)

    @staticmethod
    def probability(case: RecoveryCase, action: RecoveryAction) -> float:
        if action is RecoveryAction.DO_NOTHING:
            return 0.0
        probability = BASE_SUCCESS_PROBABILITIES[action]
        if case.is_customer_active:
            probability += 0.08
        else:
            probability -= 0.15
        if case.has_valid_payment_method:
            probability += 0.10
        else:
            probability -= 0.20
        probability -= min(case.failure_count * 0.025, 0.20)
        probability -= min(case.customer_attempt_count * 0.02, 0.12)
        probability -= min(case.days_since_failure * 0.006, 0.30)
        if case.failure_reason is FailureReason.NETWORK_ERROR:
            probability += 0.08
        elif case.failure_reason in {FailureReason.PAYMENT_METHOD_EXPIRED, FailureReason.AUTHENTICATION_FAILED}:
            probability -= 0.15
        if action is RecoveryAction.ESCALATE and case.amount >= 1000:
            probability += 0.08
        return max(0.0, min(1.0, probability))

    def simulate(self, case: RecoveryCase, action: RecoveryAction, allowed: bool = True) -> SimulatedOutcome:
        action_cost = ACTION_COSTS[action] if allowed else 0.0
        probability = self.probability(case, action) if allowed else 0.0
        recovered = allowed and action is not RecoveryAction.DO_NOTHING and self._randomizer(case, action).random() < probability
        recovered_amount = case.amount if recovered else 0.0
        net_value = recovered_amount - action_cost
        if not allowed:
            reason = "Policy violation: action was blocked and not executed."
        elif action is RecoveryAction.DO_NOTHING:
            reason = "No recovery action attempted."
        elif recovered:
            reason = "Simulated payment recovery succeeded."
        else:
            reason = "Simulated recovery attempt did not recover the payment."
        return SimulatedOutcome(
            recovered=recovered,
            recovered_amount=recovered_amount,
            action_cost=action_cost,
            net_value=net_value,
            outcome_reason=reason,
            probability=probability,
        )
