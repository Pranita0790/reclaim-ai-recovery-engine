import { useEffect, useState } from "react";
import { AlertTriangle, Check, RefreshCw, Target } from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { SectionHeader } from "../components/ui/SectionHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { getEvaluationCases, getEvaluationReplay } from "../services/api";
import type { CaseEvaluation, EvaluationReplay, ReplayCandidate } from "../types/evaluation";

const money = (value: number) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", notation: "compact", maximumFractionDigits: 1 }).format(value);
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

export function DecisionReplay() {
	const [cases, setCases] = useState<CaseEvaluation[]>([]);
	const [selectedCaseId, setSelectedCaseId] = useState("");
	const [seed, setSeed] = useState("42");
	const [replay, setReplay] = useState<EvaluationReplay | null>(null);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState(false);

	useEffect(() => {
		let cancelled = false;
		getEvaluationCases({ strategy: "RECLAIM Hybrid", limit: 100 })
			.then(nextCases => { if (!cancelled) { setCases(nextCases); if (nextCases[0]) setSelectedCaseId(nextCases[0].case_id); } })
			.catch(() => { if (!cancelled) setError(true); })
			.finally(() => { if (!cancelled) setIsLoading(false); });
		return () => { cancelled = true; };
	}, []);

	useEffect(() => {
		if (!selectedCaseId) return;
		let cancelled = false;
		setReplay(null); setError(false);
		getEvaluationReplay(selectedCaseId, Number(seed) || 42)
			.then(nextReplay => { if (!cancelled) setReplay(nextReplay); })
			.catch(() => { if (!cancelled) setError(true); });
		return () => { cancelled = true; };
	}, [selectedCaseId, seed]);

	const retry = () => { setError(false); setIsLoading(true); getEvaluationCases({ strategy: "RECLAIM Hybrid", limit: 100 }).then(nextCases => { setCases(nextCases); if (nextCases[0]) setSelectedCaseId(nextCases[0].case_id); }).catch(() => setError(true)).finally(() => setIsLoading(false)); };

	return <>
		<PageHeader eyebrow="DECISION REPLAY" title="Inspect one recovery decision" description="Trace the policy, model estimate, candidate actions, and realized outcome behind a benchmark decision." />
		<section className="panel replay-controls"><div className="replay-control"><label htmlFor="replay-case">CASE</label><select id="replay-case" value={selectedCaseId} onChange={event => setSelectedCaseId(event.target.value)} disabled={isLoading || cases.length === 0}><option value="">Select a case</option>{cases.map(item => <option key={item.case_id} value={item.case_id}>{item.case_id} · {item.selected_action}</option>)}</select></div><div className="replay-control replay-seed"><label htmlFor="replay-seed">OUTCOME SEED</label><input id="replay-seed" type="number" min="0" value={seed} onChange={event => setSeed(event.target.value)} /></div><div className="replay-count">{cases.length.toLocaleString("en-IN")} benchmark cases available</div></section>
		{error && <div className="empty-state panel evaluation-error"><AlertTriangle size={24} /><h2>Unable to load replay</h2><p>Could not retrieve this decision trace from the recovery engine.</p><button className="secondary-button" onClick={retry}><RefreshCw size={15} /> Retry</button></div>}
		{!error && !replay && <div className="skeleton large-skeleton panel" />}
		{replay && <ReplayDetails replay={replay} />}
	</>;
}

function ReplayDetails({ replay }: { replay: EvaluationReplay }) {
	const { case: replayCase, decision, candidates } = replay;
	return <><section className="replay-summary-grid"><article className="panel replay-case-panel"><SectionHeader eyebrow="CASE CONTEXT" title={replayCase.case_id} detail={`${replayCase.currency} ${replayCase.amount.toLocaleString("en-IN")} · ${replayCase.payment_status}`} /><div className="replay-facts"><Fact label="Failure reason" value={replayCase.failure_reason} /><Fact label="Days since failure" value={String(replayCase.days_since_failure)} /><Fact label="Customer attempts" value={String(replayCase.customer_attempt_count)} /><Fact label="Scenarios" value={replayCase.scenario_labels.join(", ") || "None"} /></div></article><article className="panel replay-decision-panel"><SectionHeader eyebrow="SELECTED DECISION" title={decision.selected_action} detail={decision.decision_source} /><div className="decision-status"><StatusBadge tone={decision.decision_status === "approved" ? "success" : "warning"}>{decision.decision_status}</StatusBadge><span>Confidence {percent(decision.confidence)}</span><span>ML recovery {percent(decision.ml_recovery_probability)}</span></div><p>{decision.explanation}</p></article></section><section className="panel timeline-panel"><div className="timeline-header"><SectionHeader eyebrow="ACTION COMPARISON" title="What each candidate would have produced" detail={`${candidates.length} candidates · seed ${replay.seed}`} /><StatusBadge tone="success"><Target size={12} /> Best realized action: {replay.best_realized_action}</StatusBadge></div><div className="candidate-list">{candidates.map(candidate => <CandidateRow key={candidate.action} candidate={candidate} />)}</div><div className="replay-regret"><span>REGRET FROM SELECTED ACTION</span><strong>{money(replay.regret)}</strong></div></section></>;
}

function CandidateRow({ candidate }: { candidate: ReplayCandidate }) { return <div className={`candidate-row ${candidate.is_selected ? "candidate-selected" : ""}`}><div className="candidate-action">{candidate.is_selected && <Check size={14} />}{candidate.action}</div><StatusBadge tone={candidate.is_allowed ? "success" : "danger"}>{candidate.is_allowed ? "Allowed" : "Blocked"}</StatusBadge><div><span className="candidate-label">EXPECTED</span><strong>{money(candidate.expected_value)}</strong></div><div><span className="candidate-label">REALIZED</span><strong>{money(candidate.realized_net_value)}</strong></div><div className="candidate-reason">{candidate.policy_reason || candidate.outcome_reason}</div></div>; }
function Fact({ label, value }: { label: string; value: string }) { return <div><span className="metric-label">{label}</span><strong>{value}</strong></div>; }