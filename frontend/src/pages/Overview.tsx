import { AlertTriangle, ArrowUpRight, RefreshCw, ShieldCheck, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import { MetricCard } from "../components/ui/MetricCard";
import { PageHeader } from "../components/ui/PageHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { getEvaluationCases, getEvaluationSummary } from "../services/api";
import type { CaseEvaluation, EvaluationSummary } from "../types/evaluation";

const money = (value: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", notation: "compact", maximumFractionDigits: 1 }).format(value);
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

const getStatus = (item: CaseEvaluation) => {
	if (item.recovered) return { label: "Recovered", tone: "success" as const };
	if (!item.allowed) return { label: "Policy blocked", tone: "warning" as const };
	if (item.selected_action === "DO_NOTHING") return { label: "No action", tone: "neutral" as const };
	return { label: "Evaluated", tone: "neutral" as const };
};

export function Overview() {
	const [summary, setSummary] = useState<EvaluationSummary | null>(null);
	const [cases, setCases] = useState<CaseEvaluation[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState(false);
	const [retryKey, setRetryKey] = useState(0);

	useEffect(() => {
		let cancelled = false;

		Promise.all([getEvaluationSummary(), getEvaluationCases({ limit: 4 })])
			.then(([nextSummary, nextCases]) => {
				if (cancelled) return;
				setSummary(nextSummary);
				setCases(nextCases);
				setIsLoading(false);
			})
			.catch(() => {
				if (!cancelled) {
					setError(true);
					setIsLoading(false);
				}
			});

		return () => {
			cancelled = true;
		};
	}, [retryKey]);

	if (isLoading) return <OverviewLoading />;
	if (error || !summary) {
		return <OverviewError onRetry={() => { setIsLoading(true); setError(false); setRetryKey(value => value + 1); }} />;
	}

	return <>
		<PageHeader eyebrow="OVERVIEW" title="Decision intelligence at a glance" description="Monitor how the recovery system evaluates, governs, and executes financial decisions." />
		<section className="metric-grid">
			<MetricCard label="Incremental net value" value={money(summary.incremental_net_value)} detail="vs best baseline" icon={TrendingUp} />
			<MetricCard label="Cases evaluated" value={summary.dataset_size.toLocaleString("en-IN")} detail={`${summary.strategies.length} strategies benchmarked`} icon={ArrowUpRight} />
			<MetricCard label="Policy compliance" value={percent(summary.reclaim_policy_compliance_rate)} detail="RECLAIM decisions" icon={ShieldCheck} />
		</section>
		<div className="overview-grid">
			<section className="panel quality-panel">
				<div className="section-heading"><div><div className="eyebrow">EVALUATION QUALITY</div><h2>RECLAIM benchmark results</h2></div><span className="muted">Evaluation API</span></div>
				<div className="quality-stat"><strong>{percent(summary.reclaim_recovery_rate)}</strong><span>case recovery rate for RECLAIM</span></div>
				<div className="quality-bars">
					<div><span>Case recovery</span><b style={{ width: `${summary.reclaim_recovery_rate * 100}%` }} /></div>
					<div><span>Policy compliant</span><b style={{ width: `${summary.reclaim_policy_compliance_rate * 100}%` }} /></div>
					<div><span>Regret rate</span><b style={{ width: `${summary.reclaim_regret_rate * 100}%` }} /></div>
				</div>
			</section>
		</div>
		<section className="panel table-panel">
			<div className="section-heading"><div><div className="eyebrow">EVALUATED CASES</div><h2>Latest evaluated cases</h2></div><span className="muted">Evaluation API</span></div>
			{cases.length === 0 ? <div className="empty-state"><ArrowUpRight size={24} /><h2>No evaluation cases found</h2><p>There are no backend case results available.</p></div> : <div className="table-wrap"><table><thead><tr><th>CASE</th><th>SELECTED ACTION</th><th>EXPECTED VALUE</th><th>STATUS</th><th>OUTCOME</th></tr></thead><tbody>{cases.map(item => { const status = getStatus(item); return <tr key={item.case_id}><td className="mono">{item.case_id}</td><td>{item.selected_action.replaceAll("_", " ")}</td><td className="value-cell">{money(item.expected_value)}</td><td><StatusBadge tone={status.tone}>{status.label}</StatusBadge></td><td className="value-cell"><strong>{money(item.realized_net_value)}</strong><span className="table-secondary">{item.outcome_reason || "No outcome reason"}</span></td></tr>; })}</tbody></table></div>}
		</section>
	</>;
}

function OverviewLoading() {
	return <><PageHeader eyebrow="OVERVIEW" title="Decision intelligence at a glance" description="Loading evaluation results..." /><div className="metric-grid"><div className="skeleton metric-card" /><div className="skeleton metric-card" /><div className="skeleton metric-card" /></div><div className="skeleton large-skeleton panel" /><div className="skeleton large-skeleton panel" /></>;
}

function OverviewError({ onRetry }: { onRetry: () => void }) {
	return <><PageHeader eyebrow="OVERVIEW" title="Decision intelligence at a glance" description="Monitor how the recovery system evaluates, governs, and executes financial decisions." /><div className="empty-state panel evaluation-error"><AlertTriangle size={24} /><h2>Unable to load overview</h2><p>Could not retrieve evaluation results from the recovery engine.</p><button className="secondary-button" onClick={onRetry}><RefreshCw size={15} /> Retry</button></div></>;
}
