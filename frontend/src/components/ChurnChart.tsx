import type { MetricReport } from "../types";

/** CSS-only horizontal bar chart — top N files by churn. No chart lib needed. */

function m(r: MetricReport, k: string): number {
  return (r.metrics[k]?.value as number) ?? 0;
}

interface Props {
  reports: MetricReport[];
  top?: number;
}

export default function ChurnChart({ reports, top = 15 }: Props) {
  if (!reports.length) return null;

  const sorted = [...reports]
    .sort((a, b) => m(b, "churn") - m(a, "churn"))
    .slice(0, top);

  const max = m(sorted[0], "churn") || 1;

  return (
    <section className="panel">
      <h2>Top Files by Churn</h2>
      <div className="churn-chart">
        {sorted.map((r) => {
          const churn = m(r, "churn");
          const pct = (churn / max) * 100;
          return (
            <div key={r.scope} className="churn-row">
              <span className="churn-label" title={r.scope}>
                {r.scope.split("/").pop() || r.scope}
              </span>
              <div className="churn-track">
                <div className="churn-fill" style={{ width: `${pct}%` }} />
              </div>
              <span className="churn-value">{churn.toLocaleString()}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
