import axios from "axios";

/**
 * Shared backend client. The Vite dev server proxies /api/* to FastAPI on
 * :8000 (see vite.config.ts), so no base URL is needed in development.
 */
export const api = axios.create({ baseURL: "/api" });

// TODO: typed endpoint wrappers, one per API area, e.g.
//   listRepositories(): Promise<RepositoryInfo[]>      GET    /repositories
//   uploadRepositoryZip(file: File)                    POST   /repositories/upload
//   cloneRepository(url: string)                       POST   /repositories/clone
//   listAuthors(repositoryId: string)                  GET    /authors
//   mergeAuthors(request: MergeAuthorsRequest)         POST   /authors/merge
//   fileMetrics(filter: MetricFilter)                  GET    /metrics/files
//   directoryMetrics(filter: MetricFilter)             GET    /metrics/directories
//   repositoryMetrics(filter: MetricFilter)            GET    /metrics/repository
//   commitSetMetrics(filter: MetricFilter)             GET    /metrics/commit-set
