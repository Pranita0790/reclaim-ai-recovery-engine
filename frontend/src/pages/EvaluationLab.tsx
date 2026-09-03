import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Check, RefreshCw, ShieldCheck, TrendingUp } from "lucide-react";
import { MetricCard } from "../components/ui/MetricCard";
import { PageHeader } from "../components/ui/PageHeader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { SectionHeader } from "../components/ui/SectionHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { getEvaluationMultiseed, getEvaluationScenarios, getEvaluationStrategies, getEvaluationSummary } from "../services/api";
import type { EvaluationSummary, MultiSeedStrategy, ScenarioEvaluation, StrategyEvaluation } from "../types/evaluation";

const money = (value: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", notation: "compact", maximumFractionDigits: 1 }).format(value);
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;
const points = (value: number) => `${value >= 0 ? "+" : ""}${(value * 100).toFixed(1)} pp`;

export function EvaluationLab() {
  const [summary, setSummary] = useState<EvaluationSummary | null>(null);
  const [strategies, setStrategies] = useState<StrategyEvaluation[]>([]);
  const [multiseed, setMultiseed] = useState<MultiSeedStrategy[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioEvaluation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getEvaluationSummary(), getEvaluationStrategies(), getEvaluationMultiseed(), getEvaluationScenarios()])
      .then(([nextSummary, nextStrategies, nextMultiseed, nextScenarios]) => {
        if (cancelled) return;
        setSummary(nextSummary); setStrategies(nextStrategies); setMultiseed(nextMultiseed); setScenarios(nextScenarios); setIsLoading(false);
      })
      .catch(() => { if (!cancelled) { setError(true); setIsLoading(false); } });
    return () => { cancelled = true; };
  }, [retryKey]);

  if (isLoading) return <EvaluationLoading />;
  if (error || !summary) return <EvaluationError onRetry={() => { setIsLoading(true); setError(false); setRetryKey(value => value + 1); }} />;

  const hybridMulti = multiseed.find(strategy => strategy.strategy_name === "RECLAIM Hybrid");
  const uplift = summary.reclaim_recovery_rate - summary.best_baseline_recovery_rate;

  return <>
    <PageHeader eyebrow="EVALUATION LAB" title="Measure decision quality" description="Evaluate whether financial AI decisions are economically better, policy-compliant, and stronger than available baseline strategies." action={<span className="evaluation-meta">{summary.dataset_size.toLocaleString("en-IN")} CASES · {summary.seeds.length} SEEDS · {summary.strategies.length} STRATEGIES</span>} />
    <section className="metric-grid"><MetricCard label="Recovery uplift" value={points(uplift)} detail={`vs ${summary.best_baseline ?? "best baseline"}`} icon={TrendingUp} /><MetricCard label="Net value uplift" value={money(summary.incremental_net_value)} detail="vs best baseline" icon={Activity} /><MetricCard label="Policy compliance" value={percent(summary.reclaim_policy_compliance_rate)} detail="RECLAIM decisions" icon={ShieldCheck} /></section>
    <section className="panel benchmark-panel"><SectionHeader eyebrow="STRATEGY BENCHMARK" title="How RECLAIM compares with fixed recovery strategies" detail={summary.best_baseline ? `BEST BASELINE · ${summary.best_baseline}` : "Best baseline unavailable"} /><div className="strategy-table-wrap"><table className="strategy-table"><thead><tr><th>STRATEGY</th><th>CASE RECOVERY</th><th>RECOVERED AMOUNT</th><th>NET VALUE</th><th>AVERAGE REGRET</th></tr></thead><tbody>{strategies.map(strategy => <tr className={strategy.strategy_name === "RECLAIM Hybrid" ? "strategy-winner" : ""} key={strategy.strategy_name}><td><strong>{strategy.strategy_name}</strong>{strategy.strategy_name === "RECLAIM Hybrid" && <StatusBadge tone="success"><Check size={11} /> RECLAIM</StatusBadge>}</td><td>{percent(strategy.case_recovery_rate)}</td><td className="value-cell">{money(strategy.total_recovered_amount)}</td><td className="value-cell">{money(strategy.total_net_value)}</td><td className="mono">{money(strategy.average_regret)}</td></tr>)}</tbody></table></div></section>
    {hybridMulti && <section className="panel robustness-panel"><SectionHeader eyebrow="ROBUSTNESS" title={`${summary.seeds.length} randomized evaluation runs`} detail="Multi-seed RECLAIM result" /><div className="robustness-grid"><div><span className="metric-label">Mean recovery</span><strong>{percent(hybridMulti.mean_case_recovery_rate)}</strong></div><div><span className="metric-label">Mean net value</span><strong>{money(hybridMulti.mean_net_value)}</strong></div><div><span className="metric-label">Net value variation</span><strong>{money(hybridMulti.stddev_net_value)}</strong></div></div><p className="panel-intro">The benchmark result is evaluated across several seeded runs, rather than relying on one lucky random outcome.</p></section>}
    <section className="panel scenario-panel"><SectionHeader eyebrow="SCENARIO ANALYSIS" title="Where strategy performance changes by recovery situation" detail={`${new Set(scenarios.map(item => item.scenario)).size} scenarios returned`} /><div className="scenario-grid">{groupScenarios(scenarios).map(group => <ScenarioCard key={group.scenario} scenario={group.scenario} entries={group.entries} />)}</div></section>
    <section className="evaluation-grid"><section className="panel lab-note"><div className="eyebrow">CONFIDENCE IS NOT QUALITY</div><h2>Certainty does not prove optimality</h2><p>Confidence describes how certain an agent was. Quality evaluates the decision against alternatives, policy constraints, and realized outcomes.</p><div className="method-list"><span>01 <b>Evaluate candidate actions</b></span><span>02 <b>Validate policy eligibility</b></span><span>03 <b>Measure outcome, regret, and uplift</b></span></div><p className="small-note">Decision-time estimates are evaluated separately from realized simulated outcomes.</p></section><section className="panel lab-note"><div className="eyebrow">EVALUATION METHOD</div><h2>Reproducible by design</h2><div className="method-list"><span><b>{summary.dataset_size.toLocaleString("en-IN")} synthetic cases</b></span><span><b>{summary.seeds.length} randomized seeds</b></span><span><b>{summary.strategies.length} recovery strategies</b></span><span><b>Policy-constrained alternatives</b></span><span><b>Seeded outcome simulation</b></span></div><div className="simulation-note"><AlertTriangle size={14} /><div><strong>SIMULATED OUTCOMES</strong><span>The benchmark uses reproducible simulated recovery outcomes. They represent evaluation ground truth, not live payment settlements.</span></div></div></section></section>
  </>;
}

function groupScenarios(items: ScenarioEvaluation[]) { return Array.from(items.reduce((groups, item) => { const entries = groups.get(item.scenario) ?? []; entries.push(item); groups.set(item.scenario, entries); return groups; }, new Map<string, ScenarioEvaluation[]>())).map(([scenario, entries]) => ({ scenario, entries })); }
function ScenarioCard({ scenario, entries }: { scenario: string; entries: ScenarioEvaluation[] }) { const reclaim = entries.find(item => item.strategy === "RECLAIM Hybrid"); const best = entries.reduce<ScenarioEvaluation | null>((current, item) => !current || item.total_net_value > current.total_net_value ? item : current, null); return <article className="scenario-card"><div className="scenario-card-top"><strong>{scenario.replaceAll("_", " ")}</strong>{best && <StatusBadge tone={best.strategy === "RECLAIM Hybrid" ? "success" : "neutral"}>{best.strategy} leads</StatusBadge>}</div>{reclaim && <div className="scenario-metrics"><span><b>Cases</b>{reclaim.total_cases}</span><span><b>RECLAIM recovery</b>{percent(reclaim.case_recovery_rate)}</span><span><b>RECLAIM net value</b>{money(reclaim.total_net_value)}</span><span><b>RECLAIM regret</b>{money(reclaim.average_regret)}</span></div>}<div className="scenario-compare">{entries.sort((a, b) => b.total_net_value - a.total_net_value).slice(0, 3).map(item => <div key={item.strategy}><span>{item.strategy}</span><ProgressBar value={reclaim?.total_net_value ? item.total_net_value / reclaim.total_net_value * 100 : 0} tone={item.strategy === "RECLAIM Hybrid" ? "success" : "warning"} /></div>)}</div></article>; }
function EvaluationLoading() { return <><PageHeader eyebrow="EVALUATION LAB" title="Measure decision quality" description="Loading the evaluation benchmark..." /><div className="metric-grid"><div className="skeleton metric-card" /><div className="skeleton metric-card" /><div className="skeleton metric-card" /></div><div className="skeleton large-skeleton panel" /><div className="skeleton large-skeleton panel" /></>; }
function EvaluationError({ onRetry }: { onRetry: () => void }) { return <><PageHeader eyebrow="EVALUATION LAB" title="Measure decision quality" description="Evaluate whether financial AI decisions are economically better, policy-compliant, and stronger than available baseline strategies." /><div className="empty-state panel evaluation-error"><AlertTriangle size={24} /><h2>Unable to load evaluation benchmark</h2><p>Could not retrieve evaluation results from the recovery engine.</p><button className="secondary-button" onClick={onRetry}><RefreshCw size={15} /> Retry</button></div></>; }
