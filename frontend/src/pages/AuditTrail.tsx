import { AlertTriangle, FileClock, LockKeyhole, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { SectionHeader } from "../components/ui/SectionHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { getAuditTrail, type AuditEvent } from "../services/api";

const formatTimestamp = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-IN", {
    dateStyle: "short",
    timeStyle: "medium",
  });
};

export function AuditTrail() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    getAuditTrail()
      .then((nextEvents) => {
        if (!cancelled) {
          setEvents(nextEvents);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError(true);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <PageHeader
        eyebrow="AUDIT TRAIL"
        title="Inspect system decisions"
        description="Trace every decision from case context through policy evaluation, execution, and outcome."
        action={
          <StatusBadge tone="success">
            <LockKeyhole size={12} /> Audit evidence
          </StatusBadge>
        }
      />
      <section className="panel table-panel">
        <SectionHeader
          eyebrow="EVENT HISTORY"
          title="Decision evidence"
          detail="Live audit events · UTC"
        />

        {isLoading && <div className="skeleton large-skeleton panel" />}

        {!isLoading && error && (
          <div className="empty-state panel evaluation-error">
            <AlertTriangle size={24} />
            <h2>Unable to load audit trail</h2>
            <p>Could not retrieve audit events from the recovery engine.</p>
            <button
              className="secondary-button"
              onClick={() => {
                setError(false);
                setIsLoading(true);
                getAuditTrail()
                  .then(setEvents)
                  .catch(() => setError(true))
                  .finally(() => setIsLoading(false));
              }}
            >
              <RefreshCw size={15} /> Retry
            </button>
          </div>
        )}

        {!isLoading && !error && events.length === 0 && (
          <div className="empty-state panel">
            <FileClock size={24} />
            <h2>No audit events found</h2>
            <p>There are no persisted recovery events available yet.</p>
          </div>
        )}

        {!isLoading && !error && events.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>TIMESTAMP</th>
                  <th>CASE ID</th>
                  <th>EVENT TYPE</th>
                  <th>MESSAGE</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr className="interactive-row" key={event.event_id}>
                    <td className="mono muted">{formatTimestamp(event.created_at)}</td>
                    <td className="mono table-primary">{event.case_id}</td>
                    <td>{event.event_type}</td>
                    <td className="muted">{event.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="audit-footnote">
          <FileClock size={15} /> Every event records the case context, event type, and message returned by the backend audit trail.
        </div>
      </section>
    </>
  );
}
