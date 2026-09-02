from app.models.decision import RecoveryAction


# ============================================================
# RECOVERY ACTION COSTS
# ============================================================

ACTION_COSTS: dict[RecoveryAction, float] = {
    RecoveryAction.RETRY_PAYMENT: 2.0,
    RecoveryAction.CONTACT_CUSTOMER: 15.0,
    RecoveryAction.ESCALATE: 50.0,
    RecoveryAction.DO_NOTHING: 0.0,
}


# ============================================================
# ACTION SUCCESS PROBABILITY BASELINES
#
# These are deterministic baseline values for the demo engine.
# They will later be adjusted using case-specific signals.
# ============================================================

BASE_SUCCESS_PROBABILITIES: dict[RecoveryAction, float] = {
    RecoveryAction.RETRY_PAYMENT: 0.65,
    RecoveryAction.CONTACT_CUSTOMER: 0.45,
    RecoveryAction.ESCALATE: 0.30,
    RecoveryAction.DO_NOTHING: 0.0,
}


# ============================================================
# POLICY LIMITS
# ============================================================

MAX_PAYMENT_RETRIES = 3

MAX_CUSTOMER_ATTEMPTS = 3

MAX_DAYS_FOR_AUTOMATIC_RECOVERY = 30

MIN_AMOUNT_FOR_ESCALATION = 1000.0


# ============================================================
# DECISION THRESHOLDS
# ============================================================

MIN_POSITIVE_EXPECTED_VALUE = 0.0

HIGH_CONFIDENCE_THRESHOLD = 0.80

MEDIUM_CONFIDENCE_THRESHOLD = 0.55


# ============================================================
# SYSTEM VALUES
# ============================================================

SYSTEM_ACTOR = "RECLAIM_DECISION_ENGINE"

SUPPORTED_CURRENCY = "INR"