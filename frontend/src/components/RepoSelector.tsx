import { useState } from "react";
import type { RepositoryInfo } from "../types";
import * as api from "../api/client";

interface Props {
  repos: RepositoryInfo[];
  selected: RepositoryInfo | null;
  onSelect: (r: RepositoryInfo) => void;
  onAdded: (r: RepositoryInfo) => void;
}

export default function RepoSelector({ repos, selected, onSelect, onAdded }: Props) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState<"clone" | "upload" | null>(null);
  const [error, setError] = useState("");

  const handleClone = async () => {
    if (!url.trim()) return;
    setLoading("clone");
    setError("");
    try {
      const repo = await api.cloneRepository(url.trim());
      onAdded(repo);
      setUrl("");
    } catch (e: any) {
      setError(e.response?.data?.detail ?? e.message);
    } finally {
      setLoading(null);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading("upload");
    setError("");
    try {
      const repo = await api.uploadRepositoryZip(file);
      onAdded(repo);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message);
    } finally {
      setLoading(null);
      e.target.value = "";
    }
  };

  return (
    <section className="panel repo-selector">
      <h2>Repository</h2>

      {/* Repo dropdown */}
      {repos.length > 0 && (
        <select
          className="input"
          value={selected?.id ?? ""}
          onChange={(e) => {
            const r = repos.find((r) => r.id === e.target.value);
            if (r) onSelect(r);
          }}
        >
          <option value="" disabled>Select a repository…</option>
          {repos.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name} ({r.source})
            </option>
          ))}
        </select>
      )}

      {/* Add forms */}
      <div className="add-repo-row">
        <input
          className="input"
          placeholder="https://github.com/user/repo.git"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleClone()}
          disabled={loading !== null}
        />
        <button className="btn" onClick={handleClone} disabled={loading !== null}>
          {loading === "clone" ? "Cloning…" : "Clone"}
        </button>

        <label className="btn btn-secondary file-label">
          {loading === "upload" ? "Uploading…" : "Upload ZIP"}
          <input
            type="file"
            accept=".zip"
            onChange={handleUpload}
            disabled={loading !== null}
            hidden
          />
        </label>
      </div>

      {error && <p className="error-msg">{error}</p>}
      {loading && <div className="spinner" />}
    </section>
  );
}
