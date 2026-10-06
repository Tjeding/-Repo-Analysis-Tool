# RAT Architecture

## Overview

```
                 ┌────────────────────────────────────────────┐
   Zip (.git) ──▶│              FastAPI backend               │
   Clone URL  ──▶│                                            │
                 │  api/routes ──▶ services ──▶ core          │
                 │  (REST)        (registry,   (git_service,  │
                 │                 filters)     mailmap,      │
                 │                              metrics/*)    │
                 └───────────────┬────────────────────────────┘
                                 │ JSON (OpenAPI-typed)
                 ┌───────────────▼────────────────────────────┐
                 │        React + TypeScript dashboard        │
                 │  pages ──▶ components ──▶ api/client.ts    │
                 └────────────────────────────────────────────┘
```

## Layers

### `backend/app/api/routes/` — REST surface

Thin routers only: parse/validate input via Pydantic, delegate to services,
serialize responses. No git or metric logic here.

### `backend/app/services/` — application services

- `repository_store.py` — registry of all ingested repositories
  (multi-repository support).
- `filters.py` — the shared commit filter (author, path, time period,
  manual commit list) applied by every metric query.

### `backend/app/core/` — domain core

- `git_service.py` — the only module that talks to git (GitPython):
  ingestion (deep clone, zip extraction with `.git` validation) and
  history introspection (commits, trees, diffs).
- `mailmap.py` — author identity resolution: `.mailmap` first, then manual
  merges chosen in the dashboard.
- `metrics/` — the metric engine:
  - `base.py` defines the `MetricCalculator` ABC and the registry
    (`register_metric`, `list_metrics`).
  - One module per category: `file_metrics.py`, `directory_metrics.py`,
    `repository_metrics.py`, `commit_set_metrics.py`.

### `frontend/src/` — dashboard

- `api/client.ts` — single axios instance; all backend calls go through
  typed wrappers here.
- `types/index.ts` — TS mirrors of `backend/app/models/schemas.py`.
- `components/`, `pages/` — reusable UI (filter bar, metric cards, tables)
  composed into views.

## Data flow

1. **Ingest** — user uploads a zip or submits a clone URL →
   `git_service` materializes the repo under `backend/data/repositories/<id>/`
   → registered in `repository_store` → `.mailmap` (if any) parsed.
2. **Query** — dashboard builds a `MetricFilter` → API assembles the filter →
   `git_service.iter_commits` yields filtered commits → each registered
   calculator of the requested category computes → `MetricReport[]` returned.
3. **Render** — dashboard groups reports by scope and renders panels.

## Extension points

| Want to add…           | Do this                                                        |
| ---------------------- | -------------------------------------------------------------- |
| A metric               | Subclass `MetricCalculator` in the right category module + register |
| An endpoint            | New router in `api/routes/`, include in `main.py`              |
| A dashboard view       | Page in `src/pages/` + components + `api/client.ts` wrapper    |
| Persistent repo store  | Swap `RepositoryStore` internals (JSON/SQLite) — same interface |

## Conventions

- Backend: type hints everywhere, docstrings on public functions, one
  responsibility per module, metrics stay open-ended
  (`dict[str, MetricValue]`) so the API contract never changes when the
  catalogue grows.
- Frontend: functional components, typed props, no direct `fetch` outside
  `api/client.ts`.
