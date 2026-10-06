import axios from "axios";
import type {
  RepositoryInfo,
  Author,
  MergeAuthorsRequest,
  MetricReport,
  CommitInfo,
} from "../types";

/**
 * Shared backend client. The Vite dev server proxies /api/* to FastAPI on
 * :8000 (see vite.config.ts), so no base URL is needed in development.
 */
export const api = axios.create({ baseURL: "/api" });

/* ------------------------------------------------------------------ */
/* Repositories                                                        */
/* ------------------------------------------------------------------ */

export const listRepositories = () =>
  api.get<RepositoryInfo[]>("/repositories").then((r) => r.data);

export const cloneRepository = (url: string) =>
  api.post<RepositoryInfo>("/repositories/clone", { url }).then((r) => r.data);

export const uploadRepositoryZip = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post<RepositoryInfo>("/repositories/upload", form)
    .then((r) => r.data);
};

export const listCommits = (repoId: string, ref = "HEAD") =>
  api
    .get<CommitInfo[]>("/repositories/commits", {
      params: { repository_id: repoId, ref },
    })
    .then((r) => r.data);

/* ------------------------------------------------------------------ */
/* Authors                                                             */
/* ------------------------------------------------------------------ */

export const listAuthors = (repoId: string, ref = "HEAD") =>
  api
    .get<Author[]>("/authors", { params: { repository_id: repoId, ref } })
    .then((r) => r.data);

export const mergeAuthors = (req: MergeAuthorsRequest) =>
  api.post<Author>("/authors/merge", req).then((r) => r.data);

/* ------------------------------------------------------------------ */
/* Metrics — all share the same filter params                          */
/* ------------------------------------------------------------------ */

interface MetricParams {
  repository_id: string;
  ref?: string;
  author_id?: string;
  path?: string;
  since?: string;
  until?: string;
  commits?: string[];
}

function buildParams(p: MetricParams): Record<string, string | string[]> {
  const out: Record<string, string | string[]> = {
    repository_id: p.repository_id,
  };
  if (p.ref) out.ref = p.ref;
  if (p.author_id) out.author_id = p.author_id;
  if (p.path) out.path = p.path;
  if (p.since) out.since = p.since;
  if (p.until) out.until = p.until;
  if (p.commits && p.commits.length) out.commits = p.commits;
  return out;
}

export const fileMetrics = (p: MetricParams) =>
  api
    .get<MetricReport[]>("/metrics/files", { params: buildParams(p) })
    .then((r) => r.data);

export const directoryMetrics = (p: MetricParams) =>
  api
    .get<MetricReport[]>("/metrics/directories", { params: buildParams(p) })
    .then((r) => r.data);

export const repositoryMetrics = (p: MetricParams) =>
  api
    .get<MetricReport[]>("/metrics/repository", { params: buildParams(p) })
    .then((r) => r.data);

export const commitSetMetrics = (p: MetricParams) =>
  api
    .get<MetricReport[]>("/metrics/commit-set", { params: buildParams(p) })
    .then((r) => r.data);
