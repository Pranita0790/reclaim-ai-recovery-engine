type PageHeaderProps = { eyebrow?: string; title: string; description?: string; action?: React.ReactNode };

export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return <header className="page-header">
    <div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1>{description && <p>{description}</p>}</div>
    {action}
  </header>;
}
