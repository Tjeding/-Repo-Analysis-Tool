# RAT — Repo Analysis Tool

> A web-app dashboard that measures software metrics of git repositories —
> broken down per **author**, per **file**, per **directory**, per **commit
> set**, and for the **repository as a whole**.

RAT ingests one or more git repositories, resolves author identities (via
`.mailmap` and manual merging), computes metrics from the full commit history,
and presents the results in a filterable dashboard.

---

## Quick Start

### Prerequisites

- **Python >= 3.11** (with `venv`)
- **Node.js >= 18** (with npm)
- **git** on the system PATH

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- Health check: <http://localhost:8000/api/health>
- Interactive API docs (Swagger): <http://localhost:8000/docs>

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard runs at <http://localhost:5173> and proxies `/api/*` to the backend.

### 3. Tests

```bash
cd backend
source .venv/bin/activate
python -m pytest -q           # 45 tests, <2s
```

---

## Features

| Feature | Status |
|---------|--------|
| Clone from URL (deep, full history) | Done |
| Upload ZIP (with `.git` directory) | Done |
| Multiple repositories side by side | Done |
| `.mailmap` author resolution (automatic) | Done |
| Manual author merging via UI | Done |
| File metrics (added, removed, growth, churn, modifications, mod frequency, churn rate) | Done |
| Directory metrics (recursive aggregation) | Done |
| Repository metrics (root-level summary) | Done |
| Commit-set metrics (time range or manual SHA list) | Done |
| Author metrics (per-author churn, modifications, ownership) | Done |
| Filtering: author, path prefix, since/until, manual commits | Done |
| Dashboard: repo selector, filter bar, sortable tables, summary cards, churn chart, author ownership | Done |
| Disk caching of parsed git log (JSON, instant reload) | Done |
| Rename continuity (-M50, history follows renames) | Done |

## Metric Definitions

All metrics derive from per-commit per-file primitives:

| Metric | Formula | Unit |
|--------|---------|------|
| Added lines | `l+` | lines |
| Removed lines | `l-` | lines |
| Growth | `δ = l+ - l-` | lines |
| Churn | `λ = l+ + l-` | lines |
| Modifications | `n` (commits where churn > 0) | commits |
| Modification frequency | `η = n / \|H\|` | ratio |
| Churn rate | `ρ = λ / \|H\|` | lines/commit |
| Author ownership | `ω = λ_a / λ` | ratio (0..1) |

- **Directory metrics** = recursive sum over all descendant files.
- **Repository metrics** = root directory row.
- **H̄** = non-merge commits reachable from a ref (default HEAD).
- Rename detection at 50% similarity (`-M50`); binary files excluded.
- Time filtering: `since` inclusive, `until` exclusive.
- Manual commit selection (list of SHAs) takes precedence over time range.

Full catalogue: [`docs/metrics.md`](docs/metrics.md)

## Architecture

```
Frontend (React 18 + TS + Vite)  ─── /api proxy ───►  Backend (FastAPI + Python 3.11+)
                                                        │
        RepoSelector ◄──────────── GET /repositories    │  git_service.py
        FilterBar    ◄──────────── GET /authors          │    ├─ clone / zip extract
        MetricTable  ◄──────────── GET /metrics/*        │    ├─ git log --numstat parse
        RepoSummary  ◄──────────── GET /metrics/repo     │    └─ disk + memory cache
        AuthorTable  ◄──────────── by_author in reports  │
        ChurnChart   ◄──────────── GET /metrics/files    │  engine.py (one-pass aggregation)
        AuthorManager ──────────► POST /authors/merge    │  mailmap.py (manual merge rules)
```

### Key design decisions

1. **Single subprocess parse** — `git log --numstat -M50 --no-merges -z` is
   parsed once per (repo, ref). Git's own C implementation handles diffs,
   renames, binary detection, mailmap, and merge exclusion.
2. **One-pass engine** — all five metric categories computed in a single
   traversal of the parsed commits. Directory metrics are telescoped (each
   file's primitives propagated to all ancestor directories).
3. **Disk caching** — parsed commit records are serialized to JSON in
   `backend/data/.log_cache/`. First parse of Redis (~12k commits) takes
   ~14s; subsequent loads take ~0.1s.
4. **Rename cycle safety** — alias resolution detects cycles (files renamed
   back and forth) to prevent infinite loops.

## Project Structure

```
.
├── README.md
├── docs/
│   ├── architecture.md
│   └── metrics.md
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                  ← FastAPI entry point
│   │   ├── config.py                ← settings (RAT_STORAGE_DIR, CORS)
│   │   ├── api/routes/
│   │   │   ├── repositories.py      ← list / upload / clone / commits
│   │   │   ├── authors.py           ← list / merge / unmerge
│   │   │   └── metrics.py           ← files / directories / repository / commit-set
│   │   ├── core/
│   │   │   ├── git_service.py       ← ingestion + git log parse + disk cache
│   │   │   ├── mailmap.py           ← manual author merge rules
│   │   │   └── metrics/
│   │   │       └── engine.py        ← one-pass metric aggregation
│   │   ├── models/schemas.py        ← Pydantic domain models
│   │   └── services/
│   │       ├── repository_store.py  ← multi-repo in-memory registry
│   │       └── filters.py           ← commit set selection (since/until/SHAs)
│   └── tests/
│       ├── conftest.py              ← synthetic repo fixture
│       ├── test_engine.py           ← 16 metric arithmetic tests
│       ├── test_ingestion.py        ← 13 end-to-end API tests
│       ├── test_author_merge.py     ← 16 merge/multi-repo/filter tests
│       └── test_health.py           ← smoke test
└── frontend/
    ├── package.json  vite.config.ts  tsconfig.json  index.html
    └── src/
        ├── App.tsx                  ← main dashboard (state + effects)
        ├── api/client.ts            ← typed API wrappers
        ├── types/index.ts           ← TS mirrors of backend models
        ├── index.css                ← dark theme styles
        └── components/
            ├── RepoSelector.tsx     ← repo dropdown + add forms
            ├── FilterBar.tsx        ← author/path/date/commits
            ├── MetricTable.tsx      ← sortable file/directory tables
            ├── RepoSummary.tsx      ← summary cards
            ├── AuthorTable.tsx      ← author ownership table
            ├── ChurnChart.tsx       ← CSS-only bar chart
            └── AuthorManager.tsx    ← author merge UI
```

## API Reference

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/health` | Liveness probe |
| GET | `/api/repositories` | List ingested repositories |
| POST | `/api/repositories/clone` | Deep-clone from URL |
| POST | `/api/repositories/upload` | Upload repo ZIP |
| GET | `/api/repositories/commits` | List commits (SHA, author, date, message) |
| GET | `/api/authors?repository_id=` | List canonical authors |
| POST | `/api/authors/merge` | Merge author identities |
| POST | `/api/authors/unmerge` | Revert a merge |
| GET | `/api/metrics/files` | Per-file metrics |
| GET | `/api/metrics/directories` | Per-directory metrics |
| GET | `/api/metrics/repository` | Whole-repository metrics |
| GET | `/api/metrics/commit-set` | Metrics over selected commits |

All metric endpoints accept: `repository_id` (required), `ref`, `author_id`,
`path`, `since`, `until`, `commits[]`.

## Performance

| Repository | Commits | First parse | Cached load | Aggregate |
|-----------|---------|-------------|-------------|-----------|
| cJSON | ~955 | 0.2s | <0.01s | <0.01s |
| Redis | ~12k | ~14s | 0.1s | 0.19s |

Parsed git log output is cached to disk as JSON. Subsequent page loads and
filter changes hit the cache and return in <1s.

## License

Academic project — COMS3011A, University of the Witwatersrand.
