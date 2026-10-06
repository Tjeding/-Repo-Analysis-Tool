import { useCallback, useEffect, useRef, useState } from "react";
import type { Author, MetricReport, RepositoryInfo } from "./types";
import * as api from "./api/client";

import RepoSelector from "./components/RepoSelector";
import FilterBar from "./components/FilterBar";
import MetricTable from "./components/MetricTable";
import RepoSummary from "./components/RepoSummary";
import AuthorTable from "./components/AuthorTable";
import ChurnChart from "./components/ChurnChart";
import AuthorManager from "./components/AuthorManager";

export default function App() {
  /* ---- Repo state ---- */
  const [repos, setRepos] = useState<RepositoryInfo[]>([]);
  const [repo, setRepo] = useState<RepositoryInfo | null>(null);

  /* ---- Author + filter state ---- */
  const [authors, setAuthors] = useState<Author[]>([]);
  const [authorId, setAuthorId] = useState("");
  const [path, setPath] = useState("");
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");
  const [commitShas, setCommitShas] = useState("");

  /* ---- Metric state ---- */
  const [fileReports, setFileReports] = useState<MetricReport[]>([]);
  const [dirReports, setDirReports] = useState<MetricReport[]>([]);
  const [repoReport, setRepoReport] = useState<MetricReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [metricError, setMetricError] = useState("");

  /* ---- Tab state ---- */
  const [tab, setTab] = useState<"files" | "dirs">("files");

  /* ---- Fetch counter to ignore stale responses ---- */
  const fetchId = useRef(0);

  /* ---- Load repos on mount ---- */
  useEffect(() => {
    api.listRepositories().then(setRepos).catch(() => {});
  }, []);

  /* ---- Fetch authors when repo changes ---- */
  const loadAuthors = useCallback(() => {
    if (!repo) { setAuthors([]); return; }
    api.listAuthors(repo.id).then(setAuthors).catch(() => setAuthors([]));
  }, [repo]);

  useEffect(loadAuthors, [loadAuthors]);

  /* ---- Fetch metrics when repo / filters change (debounced 300ms) ---- */
  useEffect(() => {
    if (!repo) {
      setFileReports([]);
      setDirReports([]);
      setRepoReport(null);
      return;
    }
    const id = ++fetchId.current;
    const timer = setTimeout(async () => {
      setLoading(true);
      setMetricError("");
      const params: any = { repository_id: repo.id };
      if (authorId) params.author_id = authorId;
      if (path.trim()) params.path = path.trim();
      if (since) params.since = new Date(since).toISOString();
      if (until) params.until = new Date(until).toISOString();
      const shas = commitShas.split(/[\n,]+/).map((s: string) => s.trim()).filter(Boolean);
      if (shas.length) params.commits = shas;

      try {
        const [files, dirs, repoM] = await Promise.all([
          api.fileMetrics(params),
          api.directoryMetrics(params),
          api.repositoryMetrics(params),
        ]);
        if (id !== fetchId.current) return; // stale
        setFileReports(files);
        setDirReports(dirs);
        setRepoReport(repoM[0] ?? null);
      } catch (e: any) {
        if (id !== fetchId.current) return;
        setMetricError(e.response?.data?.detail ?? e.message);
      } finally {
        if (id === fetchId.current) setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [repo, authorId, path, since, until, commitShas]);

  /* ---- Handlers ---- */
  const handleRepoAdded = (r: RepositoryInfo) => {
    setRepos((prev) => [...prev.filter((p) => p.id !== r.id), r]);
    setRepo(r);
  };

  const handleMerged = () => {
    loadAuthors();
    // Trigger metric re-fetch by bumping a dep — just re-set repo
    setRepo((r) => (r ? { ...r } : r));
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>RAT — Repo Analysis Tool</h1>
        <p>Repository metrics per author, file, directory and commit set</p>
      </header>

      <main className="app-main">
        <RepoSelector
          repos={repos}
          selected={repo}
          onSelect={setRepo}
          onAdded={handleRepoAdded}
        />

        {repo && (
          <>
            <FilterBar
              authors={authors}
              authorId={authorId} onAuthorChange={setAuthorId}
              path={path} onPathChange={setPath}
              since={since} onSinceChange={setSince}
              until={until} onUntilChange={setUntil}
              commitShas={commitShas} onCommitShasChange={setCommitShas}
            />

            {loading && <div className="loading-banner">Loading metrics…</div>}
            {metricError && <p className="error-msg panel">{metricError}</p>}

            <RepoSummary report={repoReport} />
            <AuthorTable report={repoReport} />
            <ChurnChart reports={fileReports} />

            {/* File / Directory tab toggle */}
            <div className="tab-bar">
              <button className={`tab ${tab === "files" ? "active" : ""}`} onClick={() => setTab("files")}>
                Files ({fileReports.length})
              </button>
              <button className={`tab ${tab === "dirs" ? "active" : ""}`} onClick={() => setTab("dirs")}>
                Directories ({dirReports.length})
              </button>
            </div>

            {tab === "files" && <MetricTable title="File Metrics" reports={fileReports} />}
            {tab === "dirs" && <MetricTable title="Directory Metrics" reports={dirReports} />}

            <AuthorManager
              repoId={repo.id}
              authors={authors}
              onMerged={handleMerged}
            />
          </>
        )}

        {!repo && repos.length === 0 && (
          <section className="panel empty-state">
            <h2>No repositories yet</h2>
            <p>Clone a repository URL or upload a .zip containing a .git directory to get started.</p>
          </section>
        )}
      </main>
    </div>
  );
}
