export type RecoveryRequest = {
  case_id: string;
  customer_id: string;
  amount: number;
  currency: string;
  payment_status: string;
  failure_reason: string;
  failure_count: number;
  customer_attempt_count: number;
  days_since_failure: number;
  is_customer_active: boolean;
  has_valid_payment_method: boolean;
};

export type EvaluatedAction = {
  action: string;
  is_allowed: boolean;
  success_probability: number;
  expected_recovery: number;
  expected_value: number;
  reason: string;
};

export type RecoveryResult = {
  case_id: string;
  recommended_action: string;
  decision_status: string;
  confidence: number;
  expected_recovery: number;
  expected_value: number;
  explanation: string;
  ml_recovery_probability: number;
  decision_source: string;
  policy_checks: string[];
  evaluated_actions: EvaluatedAction[];
  execution_status: string;
  execution_message: string;
  external_reference: string | null;
  final_state: string;
};
