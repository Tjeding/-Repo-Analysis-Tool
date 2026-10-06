import type { MetricReport } from "../types";

interface Props {
  report: MetricReport | null;  // repository-level report with by_author
}

export default function AuthorTable({ report }: Props) {
  if (!report || !Object.keys(report.by_author).length) return null;

  const rows = Object.entries(report.by_author)
    .map(([key, vals]) => ({
      key,
      mods: vals.author_modifications,
      churn: vals.author_churn,
      ownership: vals.author_ownership,
    }))
    .sort((a, b) => b.churn - a.churn);

  return (
    <section className="panel">
      <h2>Author Ownership</h2>
      <div className="table-wrap">
        <table className="metric-table">
          <thead>
            <tr>
              <th>Author</th>
              <th>Churn</th>
              <th>Modifications</th>
              <th>Ownership</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key}>
                <td className="cell-path">{r.key}</td>
                <td className="cell-num">{r.churn.toLocaleString()}</td>
                <td className="cell-num">{r.mods}</td>
                <td className="cell-num">{(r.ownership * 100).toFixed(1)}%</td>
                <td className="cell-bar">
                  <div
                    className="ownership-bar"
                    style={{ width: `${Math.max(r.ownership * 100, 1)}%` }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
