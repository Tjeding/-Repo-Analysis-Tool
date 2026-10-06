# RAT — Repo Analysis Tool

> A web-app dashboard that measures software metrics of git repositories —
> broken down per **author**, per **file**, per **directory**, per **commit
> set**, and for the **repository as a whole**.

RAT (Repo Analysis Tool) ingests one or more git repositories, resolves author
identities (via `.mailmap` or manual merging), computes a catalogue of metrics,
and presents the results in a filterable dashboard.

---

## Table of Contents

1. [Project Description](#project-description)
2. [Features](#features)
3. [Metric Categories](#metric-categories)
4. [Dashboard Filtering](#dashboard-filtering)
5. [Tech Stack](#tech-stack)
6. [Project Structure](#project-structure)
7. [Getting Started](#getting-started)
8. [API Overview](#api-overview)
9. [Extending RAT](#extending-rat)
10. [Roadmap](#roadmap)

---

## Project Description

Development activity in a repository is not uniform: some files change
constantly, some authors touch everything, some directories stagnate. RAT makes
that visible. Given a repository, it walks the git history and computes metrics
at four granularities:

| Granularity   | Question it answers                                   |
| ------------- | ----------------------------------------------------- |
| **Author**    | How much has each developer contributed, and where?   |
| **File**      | Which files are churning, growing, or risky?          |
| **Directory** | Which areas of the codebase are most active?          |
| **Repository**| How healthy/active is the project overall?            |

Results are exposed through a REST API and rendered on a dashboard that can be
filtered by repository, author, file/directory, and by commits — either a time
period or a manually selected list of commits.

### Repository input

A repository can be provided in two forms:

1. **Zip upload** — a `.zip` of the working tree that **includes the `.git`
   directory**, so full history is available.
2. **Remote URL** — the repository is **deeply cloned** (full history, not a
   shallow clone) from the given URL.

### Author merging

Not every commit by the same person shares one author identity (different
emails, spellings, machines). RAT resolves identities in two stages:

1. **`.mailmap`** — if the repository ships a
   [`.mailmap`](https://git-scm.com/docs/gitmailmap) file, its mappings are
   applied automatically.
2. **Manual merging** — regardless of whether a mailmap exists, the user can
   merge arbitrary authors together in the dashboard.

## Features

- **Repository Upload** — ingest via zip file (with `.git`) or clone URL.
- **Multiple Repository Support** — several repositories registered side by
  side; the dashboard switches between them.
- **Author Merging** — automatic via `.mailmap`, manual via the UI.
- **Metric Categories** — File, Directory, Repository, and Commit Set metrics
  (see below).
- **Filtering** — every metric query accepts the common filter set
  (repository, author, path, time range, explicit commit list).

> Note: the metric modules and ingestion services are currently **stubs** —
> this repository is the initialized skeleton. See [Roadmap](#roadmap).

## Metric Categories

The exact metric definitions are specified in the course brief; each one is
implemented as a small, pluggable *calculator* so the catalogue is easy to
extend. The four categories:

- **File Metrics** — computed for every file in scope
  (e.g. churn, size, authorship for that file).
- **Directory Metrics** — aggregated per directory over the files it contains.
- **Repository Metrics** — single values describing the whole repository.
- **Commit Set Metrics** — computed over an arbitrary set of commits (a time
  period or a hand-picked list).

Concrete definitions live in [`docs/metrics.md`](docs/metrics.md) and are
implemented under `backend/app/core/metrics/`.

## Dashboard Filtering

Every view/query can be filtered by:

- **Repository** — any ingested repository.
- **Author** — canonical (merged) author.
- **File or directory** — a path prefix within the repository.
- **Commits** —
  - a **time period** (`since` / `until`), or
  - a **manually selected list of commits**.

## Tech Stack

| Layer     | Choice                                        | Why                                             |
| --------- | --------------------------------------------- | ----------------------------------------------- |
| Backend   | Python 3.11+, FastAPI, GitPython, Pydantic v2 | Mature git analysis + typed async API + OpenAPI |
| Frontend  | React 18, TypeScript, Vite, Axios             | Fast dashboard DX, typed API client             |
| Testing   | pytest (backend)                              | Standard, integrates with FastAPI TestClient    |
| Monorepo  | `backend/` + `frontend/` + `docs/`            | Clear separation, independent tooling           |

## Project Structure

```
.
├── README.md                     ← you are here
├── docs/
│   ├── architecture.md           ← layers, data flow, extension points
│   └── metrics.md                ← metric catalogue per category
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py               ← FastAPI entry point (health check live)
│   │   ├── config.py             ← settings (storage dir, CORS, env: RAT_*)
│   │   ├── api/routes/           ← REST surface (stubs)
│   │   │   ├── repositories.py   ←   list / upload zip / clone URL
│   │   │   ├── authors.py        ←   list / manual merge
│   │   │   └── metrics.py        ←   file / directory / repo / commit-set
│   │   ├── core/
│   │   │   ├── git_service.py    ← clone & zip extraction (stub)
│   │   │   ├── mailmap.py        ← identity resolution (stub)
│   │   │   └── metrics/
│   │   │       ├── base.py       ← MetricCalculator ABC + registry ★
│   │   │       ├── file_metrics.py
│   │   │       ├── directory_metrics.py
│   │   │       ├── repository_metrics.py
│   │   │       └── commit_set_metrics.py
│   │   ├── models/schemas.py     ← Pydantic domain models
│   │   └── services/
│   │       ├── repository_store.py ← multi-repo registry (stub)
│   │       └── filters.py        ← shared commit filtering (stub)
│   └── tests/                    ← pytest
└── frontend/
    ├── package.json  vite.config.ts  tsconfig.json  index.html
    └── src/
        ├── App.tsx               ← dashboard shell (placeholder panels)
        ├── api/client.ts         ← typed backend client (stub)
        ├── types/index.ts        ← TS mirrors of the API models
        ├── components/           ← filter bar, metric cards, tables…
        └── pages/                ← dashboard, authors, files views…
```

★ `core/metrics/base.py` is the main extension point — see
[Extending RAT](#extending-rat).

## Getting Started

### Prerequisites

- Python ≥ 3.11 (with `venv`)
- Node.js ≥ 18 (with npm)
- `git` available on the system PATH

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- Health check: <http://localhost:8000/api/health>
- Interactive API docs: <http://localhost:8000/docs>

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard runs at <http://localhost:5173> and proxies `/api/*` to the backend
on port 8000 (see `frontend/vite.config.ts`).

### Tests

```bash
cd backend && pytest
```

## API Overview

Planned REST surface (stubs exist at these routes):

| Method | Route                       | Purpose                                  |
| ------ | --------------------------- | ---------------------------------------- |
| GET    | `/api/health`               | Liveness probe ✅ implemented            |
| GET    | `/api/repositories`         | List ingested repositories               |
| POST   | `/api/repositories/upload`  | Ingest a repo zip (must contain `.git`)  |
| POST   | `/api/repositories/clone`   | Deep-clone a repo from a remote URL      |
| GET    | `/api/authors`              | List canonical authors of a repository   |
| POST   | `/api/authors/merge`        | Manually merge author identities         |
| GET    | `/api/metrics/files`        | Per-file metrics (filtered)              |
| GET    | `/api/metrics/directories`  | Per-directory metrics (filtered)         |
| GET    | `/api/metrics/repository`   | Whole-repository metrics (filtered)      |
| GET    | `/api/metrics/commit-set`   | Metrics over a selected set of commits   |

All metric endpoints accept the shared filter: `repository_id`, `author_id`,
`path`, `since`, `until`, `commits[]`.

## Extending RAT

**Adding a new metric** — subclass `MetricCalculator` in the matching category
module and register it:

```python
# backend/app/core/metrics/file_metrics.py
from app.core.metrics.base import MetricCalculator, register_metric
from app.models.schemas import MetricCategory, MetricFilter, MetricReport

class LinesOfCode(MetricCalculator):
    key = "loc"
    category = MetricCategory.FILE
    description = "Lines of code per file"

    def calculate(self, repo_path, filters: MetricFilter) -> MetricReport:
        ...  # walk repo_path constrained by filters

register_metric(LinesOfCode())
```

The API layer discovers registered calculators automatically — no route
changes needed.

**Adding an endpoint** — create a router in `backend/app/api/routes/` and
include it in `backend/app/main.py`.

**Adding a dashboard view** — add a page under `frontend/src/pages/`, compose
components from `frontend/src/components/`, call the backend through
`frontend/src/api/client.ts`.

## Roadmap

- [ ] Repository ingestion: zip extraction + deep clone (`core/git_service.py`)
- [ ] Multi-repository registry (`services/repository_store.py`)
- [ ] `.mailmap` parsing + manual author merging (`core/mailmap.py`)
- [ ] Commit filtering: author / path / time range / explicit list
      (`services/filters.py`)
- [ ] File / Directory / Repository / Commit Set metric calculators
- [ ] Dashboard: repository selector, filter bar, metric panels
- [ ] Manual commit selection UI
