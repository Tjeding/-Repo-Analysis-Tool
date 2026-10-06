import { useState } from "react";
import type { MetricReport } from "../types";

type SortKey = "scope" | "added_lines" | "removed_lines" | "growth" | "churn" | "modifications" | "modification_frequency" | "churn_rate";

function m(r: MetricReport, k: string): number {
  return (r.metrics[k]?.value as number) ?? 0;
}

function fmt(v: number): string {
  if (Number.isInteger(v)) return v.toLocaleString();
  return v.toFixed(4);
}

interface Props {
  title: string;
  reports: MetricReport[];
}

export default function MetricTable({ title, reports }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("churn");
  const [asc, setAsc] = useState(false);

  const toggle = (k: SortKey) => {
    if (k === sortKey) setAsc(!asc);
    else { setSortKey(k); setAsc(false); }
  };

  const sorted = [...reports].sort((a, b) => {
    let va: number | string, vb: number | string;
    if (sortKey === "scope") { va = a.scope; vb = b.scope; }
    else { va = m(a, sortKey); vb = m(b, sortKey); }
    const cmp = va < vb ? -1 : va > vb ? 1 : 0;
    return asc ? cmp : -cmp;
  });

  const cols: { key: SortKey; label: string }[] = [
    { key: "scope", label: "Path" },
    { key: "added_lines", label: "Added" },
    { key: "removed_lines", label: "Removed" },
    { key: "growth", label: "Growth" },
    { key: "churn", label: "Churn" },
    { key: "modifications", label: "Mods" },
    { key: "modification_frequency", label: "Mod Freq" },
    { key: "churn_rate", label: "Churn Rate" },
  ];

  const arrow = (k: SortKey) => (k === sortKey ? (asc ? " ▲" : " ▼") : "");

  if (!reports.length) return null;

  return (
    <section className="panel">
      <h2>{title}</h2>
      <div className="table-wrap">
        <table className="metric-table">
          <thead>
            <tr>
              {cols.map((c) => (
                <th key={c.key} onClick={() => toggle(c.key)} className="sortable">
                  {c.label}{arrow(c.key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.scope}>
                <td className="cell-path">{r.scope}</td>
                <td className="cell-num">{fmt(m(r, "added_lines"))}</td>
                <td className="cell-num">{fmt(m(r, "removed_lines"))}</td>
                <td className="cell-num">{fmt(m(r, "growth"))}</td>
                <td className="cell-num cell-churn">{fmt(m(r, "churn"))}</td>
                <td className="cell-num">{fmt(m(r, "modifications"))}</td>
                <td className="cell-num">{fmt(m(r, "modification_frequency"))}</td>
                <td className="cell-num">{fmt(m(r, "churn_rate"))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
