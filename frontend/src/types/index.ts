/**
 * TypeScript mirrors of the backend API models
 * (backend/app/models/schemas.py). Keep these in sync with the backend.
 */

export type RepositorySource = "zip" | "url";

export interface RepositoryInfo {
  id: string;
  name: string;
  source: RepositorySource;
  path: string;
  default_branch: string | null;
}

export interface AuthorIdentity {
  name: string;
  email: string;
}

export interface Author {
  id: string;
  name: string;
  email: string;
  identities: AuthorIdentity[];
}

export interface MergeAuthorsRequest {
  repository_id: string;
  author_ids: string[];
  canonical?: AuthorIdentity | null;
}

export interface CommitInfo {
  sha: string;
  author: AuthorIdentity;
  timestamp: string; // ISO 8601
  message: string;
}

export interface MetricFilter {
  repository_id: string;
  ref?: string; // defines H̄ — defaults to HEAD
  author_id?: string | null;
  path?: string | null;
  since?: string | null; // ISO 8601, inclusive
  until?: string | null; // ISO 8601, exclusive
  commits?: string[] | null; // manual commit selection (SHAs), takes precedence
}

export type MetricCategory = "file" | "directory" | "repository" | "commit_set";

export interface MetricValue {
  value: number;
  unit?: string | null;
  description?: string | null;
}

export interface AuthorMetricValues {
  author_modifications: number;
  author_churn: number;
  author_ownership: number; // 0..1
}

export interface MetricReport {
  category: MetricCategory;
  scope: string;
  metrics: Record<string, MetricValue>;
  by_author: Record<string, AuthorMetricValues>;
}
