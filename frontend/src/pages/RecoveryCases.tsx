import { ArrowUpRight, BriefcaseBusiness } from "lucide-react";
import { PageHeader } from "../components/ui/PageHeader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { SectionHeader } from "../components/ui/SectionHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { recoveryCases } from "../data/mockDecisionData";

export function RecoveryCases() {
  return <><PageHeader eyebrow="RECOVERY CASES" title="Case operations" description="Review active payment recovery decisions, their quality scores, and verified outcomes." action={<button className="secondary-button"><BriefcaseBusiness size={15} /> 342 active cases</button>} /><section className="panel table-panel"><SectionHeader eyebrow="CASE QUEUE" title="Latest evaluated cases" detail="Demo data · synced moments ago" /><div className="table-wrap"><table><thead><tr><th>CASE / CUSTOMER</th><th>AMOUNT</th><th>SELECTED ACTION</th><th>QUALITY</th><th>STATUS</th><th>OUTCOME</th><th /></tr></thead><tbody>{recoveryCases.map(item => <tr className="interactive-row" key={item.id}><td><strong className="table-primary">{item.id}</strong><span className="table-secondary">{item.customer}</span></td><td className="mono">{item.amount}</td><td>{item.action.replaceAll("_", " ")}</td><td><div className="table-progress"><span>{item.quality}</span><ProgressBar value={item.quality} /></div></td><td><StatusBadge tone={item.status === "Policy blocked" ? "warning" : item.status === "Executing" ? "neutral" : "success"}>{item.status}</StatusBadge></td><td className="value-cell">{item.outcome}</td><td><button className="icon-button" aria-label={`Open ${item.id}`}><ArrowUpRight size={15} /></button></td></tr>)}</tbody></table></div></section></>;
}
