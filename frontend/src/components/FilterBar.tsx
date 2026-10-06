import type { Author } from "../types";

interface Props {
  authors: Author[];
  authorId: string;
  onAuthorChange: (v: string) => void;
  path: string;
  onPathChange: (v: string) => void;
  since: string;
  onSinceChange: (v: string) => void;
  until: string;
  onUntilChange: (v: string) => void;
  commitShas: string;
  onCommitShasChange: (v: string) => void;
}

export default function FilterBar({
  authors, authorId, onAuthorChange,
  path, onPathChange,
  since, onSinceChange,
  until, onUntilChange,
  commitShas, onCommitShasChange,
}: Props) {
  return (
    <section className="panel filter-bar">
      <h2>Filters</h2>
      <div className="filter-grid">
        {/* Author */}
        <label className="filter-field">
          <span className="filter-label">Author</span>
          <select className="input" value={authorId} onChange={(e) => onAuthorChange(e.target.value)}>
            <option value="">All authors</option>
            {authors.map((a) => (
              <option key={a.id} value={`${a.name} <${a.email}>`}>
                {a.name}
              </option>
            ))}
          </select>
        </label>

        {/* Path */}
        <label className="filter-field">
          <span className="filter-label">Path prefix</span>
          <input
            className="input"
            placeholder="e.g. src/core"
            value={path}
            onChange={(e) => onPathChange(e.target.value)}
          />
        </label>

        {/* Since */}
        <label className="filter-field">
          <span className="filter-label">Since (inclusive)</span>
          <input
            className="input"
            type="datetime-local"
            value={since}
            onChange={(e) => onSinceChange(e.target.value)}
          />
        </label>

        {/* Until */}
        <label className="filter-field">
          <span className="filter-label">Until (exclusive)</span>
          <input
            className="input"
            type="datetime-local"
            value={until}
            onChange={(e) => onUntilChange(e.target.value)}
          />
        </label>

        {/* Manual commits */}
        <label className="filter-field filter-field-wide">
          <span className="filter-label">Commit SHAs (one per line)</span>
          <textarea
            className="input"
            rows={2}
            placeholder="abc1234&#10;def5678"
            value={commitShas}
            onChange={(e) => onCommitShasChange(e.target.value)}
          />
        </label>
      </div>
    </section>
  );
}
