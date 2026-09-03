import { AlertTriangle, ArrowUpRight, BriefcaseBusiness, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { PageHeader } from "../components/ui/PageHeader";
import { SectionHeader } from "../components/ui/SectionHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { getEvaluationCases } from "../services/api";
import type { CaseEvaluation } from "../types/evaluation";

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number.isFinite(value) ? value : 0);

const deriveStatus = (item: CaseEvaluation) => {
  if (item.recovered) {
    return { tone: "success" as const, label: "Recovered" };
  }

  if (!item.allowed) {
    return { tone: "warning" as const, label: "Policy blocked" };
  }

  if (item.selected_action === "DO_NOTHING") {
    return { tone: "neutral" as const, label: "No action" };
  }

  return { tone: "neutral" as const, label: "Evaluated" };
};

export function RecoveryCases() {
  const [cases, setCases] = useState<CaseEvaluation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    getEvaluationCases({ limit: 100 })
      .then((nextCases) => {
        if (!cancelled) {
          setCases(nextCases);
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

  const retry = () => {
    setError(false);
    setIsLoading(true);

    getEvaluationCases({ limit: 100 })
      .then(setCases)
      .catch(() => setError(true))
      .finally(() => setIsLoading(false));
  };

  return (
    <>
      <PageHeader
        eyebrow="RECOVERY CASES"
        title="Case operations"
        description="Review backend-evaluated recovery decisions, expected value, and realized outcomes."
        action={
          <button className="secondary-button">
            <BriefcaseBusiness size={15} /> {isLoading ? "Loading cases" : `${cases.length} evaluated cases shown`}
          </button>
        }
      />

      <section className="panel table-panel">
        <SectionHeader
          eyebrow="CASE QUEUE"
          title="Latest evaluated cases"
          detail={isLoading ? "Loading live data" : "Live evaluation data"}
        />

        {isLoading && <div className="skeleton large-skeleton panel" />}

        {!isLoading && error && (
          <div className="empty-state panel evaluation-error">
            <AlertTriangle size={24} />
            <h2>Unable to load recovery cases</h2>
            <p>Could not retrieve the live evaluation case set from the recovery engine.</p>
            <button className="secondary-button" onClick={retry}>
              <RefreshCw size={15} /> Retry
            </button>
          </div>
        )}

        {!isLoading && !error && cases.length === 0 && (
          <div className="empty-state panel">
            <BriefcaseBusiness size={24} />
            <h2>No evaluation cases found</h2>
            <p>There are no backend case results available for the current configuration.</p>
          </div>
        )}

        {!isLoading && !error && cases.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>CASE</th>
                  <th>EXPECTED VALUE</th>
                  <th>SELECTED ACTION</th>
                  <th>STATUS</th>
                  <th>OUTCOME</th>
                  <th>REGRET</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {cases.map((item) => {
                  const status = deriveStatus(item);

                  return (
                    <tr className="interactive-row" key={item.case_id}>
                      <td>
                        <strong className="table-primary">{item.case_id}</strong>
                        <span className="table-secondary">{item.strategy}</span>
                      </td>
                      <td className="mono">{formatCurrency(item.expected_value)}</td>
                      <td>{item.selected_action.replaceAll("_", " ")}</td>
                      <td>
                        <StatusBadge tone={status.tone}>{status.label}</StatusBadge>
                      </td>
                      <td className="value-cell">
                        <strong>{item.recovered ? formatCurrency(item.recovered_amount) : formatCurrency(0)}</strong>
                        <span className="table-secondary">{item.outcome_reason || "No outcome reason"}</span>
                      </td>
                      <td className="mono">{formatCurrency(item.regret)}</td>
                      <td>
                        <button className="icon-button" aria-label={`Open ${item.case_id}`}>
                          <ArrowUpRight size={15} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
