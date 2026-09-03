type ProgressBarProps = { value: number; tone?: "success" | "warning" };

export function ProgressBar({ value, tone = "success" }: ProgressBarProps) {
  return <span className={`progress-track progress-${tone}`}><i style={{ width: `${Math.min(100, Math.max(0, value))}%` }} /></span>;
}
