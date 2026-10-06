import type { MetricReport } from "../types";

function m(r: MetricReport, k: string): number {
  return (r.metrics[k]?.value as number) ?? 0;
}

function fmt(v: number): string {
  if (Number.isInteger(v)) return v.toLocaleString();
  return v.toFixed(2);
}

interface Props {
  report: MetricReport | null;
}

export default function RepoSummary({ report }: Props) {
  if (!report) return null;

  const cards: { label: string; value: string; color: string }[] = [
    { label: "Total Churn", value: fmt(m(report, "churn")) + " lines", color: "#e74c3c" },
    { label: "Net Growth", value: fmt(m(report, "growth")) + " lines", color: "#2ecc71" },
    { label: "Added", value: fmt(m(report, "added_lines")) + " lines", color: "#3498db" },
    { label: "Removed", value: fmt(m(report, "removed_lines")) + " lines", color: "#e67e22" },
    { label: "Modifications", value: fmt(m(report, "modifications")) + " commits", color: "#9b59b6" },
    { label: "Churn Rate", value: fmt(m(report, "churn_rate")) + " l/c", color: "#1abc9c" },
  ];

  return (
    <section className="panel">
      <h2>Repository Summary</h2>
      <div className="summary-grid">
        {cards.map((c) => (
          <div key={c.label} className="summary-card" style={{ borderTopColor: c.color }}>
            <span className="summary-value">{c.value}</span>
            <span className="summary-label">{c.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
