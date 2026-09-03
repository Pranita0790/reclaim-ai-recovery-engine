type StatusBadgeProps = { children: React.ReactNode; tone?: "neutral" | "success" | "warning" | "danger" };

export function StatusBadge({ children, tone = "neutral" }: StatusBadgeProps) {
  return <span className={`status-badge status-${tone}`}><span className="status-dot" />{children}</span>;
}
