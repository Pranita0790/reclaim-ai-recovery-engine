export type EvaluationSummary = {
  dataset_size: number;
  seeds: number[];
  strategies: string[];
  best_baseline: string | null;
  reclaim_recovery_rate: number;
  best_baseline_recovery_rate: number;
  incremental_recovered_amount: number;
  incremental_net_value: number;
  reclaim_policy_compliance_rate: number;
  reclaim_average_regret: number;
  reclaim_regret_rate: number;
};

export type StrategyEvaluation = {
  strategy_name: string;
  total_cases: number;
  case_recovery_rate: number;
  attempt_rate: number;
  attempt_recovery_rate: number;
  total_recovered_amount: number;
  total_action_cost: number;
  total_net_value: number;
  average_net_value_per_case: number;
  policy_violations: number;
  policy_compliance_rate: number;
  average_regret: number;
  regret_rate: number;
  average_normalized_regret: number;
  expected_recovery_absolute_error: number;
  expected_value_absolute_error: number;
  action_distribution: Record<string, number>;
};

export type MultiSeedStrategy = {
  strategy_name: string;
  mean_case_recovery_rate: number;
  mean_recovered_amount: number;
  mean_net_value: number;
  mean_policy_violations: number;
  mean_regret: number;
  stddev_net_value: number;
  minimum_net_value: number;
  maximum_net_value: number;
};

export type ScenarioEvaluation = {
  scenario: string;
  strategy: string;
  total_cases: number;
  case_recovery_rate: number;
  total_recovered_amount: number;
  total_net_value: number;
  policy_violations: number;
  average_regret: number;
};

export type CaseEvaluation = {
  case_id: string;
  strategy: string;
  scenario_labels: string[];
  selected_action: string;
  allowed: boolean;
  expected_recovery: number;
  expected_value: number;
  recovered: boolean;
  recovered_amount: number;
  action_cost: number;
  realized_net_value: number;
  regret: number;
  outcome_reason: string;
};

export type ReplayCase = {
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
  scenario_labels: string[];
};

export type ReplayDecision = {
  selected_action: string;
  decision_status: string;
  confidence: number;
  ml_recovery_probability: number;
  decision_source: string;
  explanation: string;
};

export type ReplayCandidate = {
  action: string;
  is_allowed: boolean;
  policy_reason: string;
  success_probability: number;
  expected_recovery: number;
  expected_value: number;
  action_cost: number;
  recovered: boolean;
  recovered_amount: number;
  realized_net_value: number;
  outcome_reason: string;
  is_selected: boolean;
};

export type EvaluationReplay = {
  case: ReplayCase;
  strategy: string;
  seed: number;
  decision: ReplayDecision;
  candidates: ReplayCandidate[];
  regret: number;
  best_realized_action: string;
  best_realized_net_value: number;
};
