import type { LucideIcon } from "lucide-react";

type MetricCardProps = { label: string; value: string; detail: string; icon: LucideIcon };

export function MetricCard({ label, value, detail, icon: Icon }: MetricCardProps) {
  return <article className="metric-card"><div className="metric-card-top"><span className="metric-label">{label}</span><Icon size={16} /></div><strong>{value}</strong><span className="metric-detail">{detail}</span></article>;
}
