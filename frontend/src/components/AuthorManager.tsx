import { useState } from "react";
import type { Author } from "../types";
import * as api from "../api/client";

interface Props {
  repoId: string;
  authors: Author[];
  onMerged: () => void;
}

export default function AuthorManager({ repoId, authors, onMerged }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const toggle = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleMerge = async () => {
    if (selected.size < 2) return;
    setLoading(true);
    setError("");
    try {
      await api.mergeAuthors({
        repository_id: repoId,
        author_ids: [...selected],
      });
      setSelected(new Set());
      onMerged();
    } catch (e: any) {
      setError(e.response?.data?.detail ?? e.message);
    } finally {
      setLoading(false);
    }
  };

  if (!authors.length) return null;

  return (
    <section className="panel">
      <h2>Author Management</h2>
      <p className="hint">Select 2+ authors and merge them into one canonical identity.</p>
      <div className="author-list">
        {authors.map((a) => {
          const key = `${a.name} <${a.email}>`;
          return (
            <label key={a.id} className="author-item">
              <input
                type="checkbox"
                checked={selected.has(key)}
                onChange={() => toggle(key)}
              />
              <span>{a.name}</span>
              <span className="author-email">&lt;{a.email}&gt;</span>
              {a.identities.length > 1 && (
                <span className="author-badge">{a.identities.length} ids</span>
              )}
            </label>
          );
        })}
      </div>
      <button
        className="btn"
        disabled={selected.size < 2 || loading}
        onClick={handleMerge}
      >
        {loading ? "Merging…" : `Merge ${selected.size} authors`}
      </button>
      {error && <p className="error-msg">{error}</p>}
    </section>
  );
}
