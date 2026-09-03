import type { RecoveryRequest, RecoveryResult } from "../types/recovery";
import type { CaseEvaluation, EvaluationReplay, EvaluationSummary, MultiSeedStrategy, ScenarioEvaluation, StrategyEvaluation } from "../types/evaluation";

const API_BASE_URL = "/api/v1";

async function getJson<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch {
    throw new Error("Unable to load evaluation benchmark");
  }
  if (!response.ok) {
    throw new Error("Unable to load evaluation benchmark");
  }
  return response.json() as Promise<T>;
}

export function getEvaluationSummary(): Promise<EvaluationSummary> {
  return getJson<EvaluationSummary>("/evaluation/summary");
}

export function getEvaluationStrategies(): Promise<StrategyEvaluation[]> {
  return getJson<StrategyEvaluation[]>("/evaluation/strategies");
}

export function getEvaluationMultiseed(): Promise<MultiSeedStrategy[]> {
  return getJson<MultiSeedStrategy[]>("/evaluation/multiseed");
}

export function getEvaluationScenarios(strategy?: string): Promise<ScenarioEvaluation[]> {
  const query = strategy ? `?strategy=${encodeURIComponent(strategy)}` : "";
  return getJson<ScenarioEvaluation[]>(`/evaluation/scenarios${query}`);
}

export function getEvaluationCases(options: { strategy?: string; scenario?: string; limit?: number } = {}): Promise<CaseEvaluation[]> {
  const query = new URLSearchParams();
  if (options.strategy) query.set("strategy", options.strategy);
  if (options.scenario) query.set("scenario", options.scenario);
  if (options.limit !== undefined) query.set("limit", String(options.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return getJson<CaseEvaluation[]>(`/evaluation/cases${suffix}`);
}

export function getEvaluationReplay(caseId: string, seed = 42): Promise<EvaluationReplay> {
  return getJson<EvaluationReplay>(`/evaluation/replay/${encodeURIComponent(caseId)}?seed=${seed}`);
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch("/health");
    return response.ok;
  } catch {
    return false;
  }
}

export async function processRecoveryCase(
  payload: RecoveryRequest,
): Promise<RecoveryResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/recovery/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Request failed.";
    throw new Error(`Unable to reach recovery engine: ${detail}`);
  }

  if (!response.ok) {
    let message = "Unable to process recovery case.";
    try {
      const errorData = await response.json();
      message = errorData.message || errorData.detail || message;
    } catch {
      // Keep the default message when the server response is not JSON.
    }
    throw new Error(`Unable to reach recovery engine: ${message}`);
  }

  return response.json() as Promise<RecoveryResult>;
}
