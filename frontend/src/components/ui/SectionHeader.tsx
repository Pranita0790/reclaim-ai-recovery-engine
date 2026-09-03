type SectionHeaderProps = { eyebrow: string; title: string; detail?: string };

export function SectionHeader({ eyebrow, title, detail }: SectionHeaderProps) {
  return <div className="section-heading"><div><div className="eyebrow">{eyebrow}</div><h2>{title}</h2></div>{detail && <span className="muted">{detail}</span>}</div>;
}
