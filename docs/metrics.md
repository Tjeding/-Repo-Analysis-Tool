# RAT Metric Catalogue

Authoritative metric definitions from the COMS3011A brief. Every metric is a
`MetricCalculator` (see `backend/app/core/metrics/base.py`) and appears in API
responses under `MetricReport.metrics` keyed by the `Key` below.

## Preliminaries (commit model)

- Commit `h`: author `h[a]` (after merging), previous commit `h[p]`
  (initial commit's parent is the empty commit), `h[committer-date]`,
  files `h[F]`, directories `h[D]`.
- `H̄` = **non-merge** commits reachable from the reference commit (usually
  HEAD).
- `H_t` = `{h ∈ H̄ | t ≤ committer-date}`; `H_i,j` = `{h ∈ H̄ | i ≤ date < j}`
  (since **inclusive**, until **exclusive**).
- `H[F]`, `H[D]` = union of files/dirs over each `h ∈ H` **and its parent**
  (so deleted/renamed objects still appear).
- **Binary files are not measured** (git's binary detection).
- **Rename detection at 50%**: a rename keeps the object's metrics; changes
  are attributed to the **new** path.
- **Deletions**: an object present in `h[p]` but not `h` records its removed
  lines on its path.
- Per-commit file primitives: `l+` (added lines), `l−` (removed lines).

## File Metrics (per commit `h`, file `f`)

| Key | Name | Definition |
| --- | ---- | ---------- |
| `added_lines` | File Added Lines | `l+_{h,f}` |
| `removed_lines` | File Removed Lines | `l−_{h,f}` |
| `growth` | File Growth | `δ = l+ − l−` |
| `churn` | File Churn | `λ = l+ + l−` |

## Directory Metrics (per commit `h`, directory `d`)

Recursive sums over **immediate** files and subdirectories — equivalent to
summing each descendant file's primitives into every ancestor directory.

| Key | Name | Definition |
| --- | ---- | ---------- |
| `added_lines` | Directory Added Lines | `Σ l+` over immediate files + subdirs |
| `removed_lines` | Directory Removed Lines | `Σ l−` likewise |
| `growth` | Directory Growth | `Σ δ` likewise |
| `churn` | Directory Churn | `Σ λ` likewise |

## Repository Metrics

Directory metrics evaluated on the **root** of the commit tree.

| Key | Name |
| --- | ---- |
| `added_lines`, `removed_lines`, `growth`, `churn` | as above, on root |

## Commit Set Metrics (over commit set `H`, object `o ∈ H[F] ∪ H[D]`)

| Key | Name | Definition |
| --- | ---- | ---------- |
| `added_lines` | Added lines over `H` | `Σ_{h∈H} l+_{h,o}` |
| `removed_lines` | Removed lines over `H` | `Σ l−_{h,o}` |
| `growth` | Growth over `H` | `Σ δ_{h,o}` |
| `churn` | Churn over `H` | `λ_{H,o} = Σ λ_{h,o}` |
| `modifications` | Modifications | `n_{H,o} = #{h ∈ H : λ_{h,o} > 0}` |
| `modification_frequency` | Modification frequency | `η = n/|H|` (0 if `|H| = 0`) |
| `churn_rate` | Churn rate | `ρ = λ_{H,o}/|H|` (0 if `|H| = 0`) |

## Author Metrics (author `a`, indicator `𝕀(a,h) = 1 iff a = h[a]`)

| Key | Name | Definition |
| --- | ---- | ---------- |
| `author_modifications` | Author Modifications | `n_{H,o,a} = Σ_h 𝕀(a,h)·𝕀_n(h,o)` |
| `author_churn` | Author Churn | `λ_{H,o,a} = Σ_h λ_{h,o}·𝕀(a,h)` |
| `author_ownership` | Author Ownership | `ω = λ_{H,o,a} / λ_{H,o}` (0 if `λ_{H,o} = 0`) |

## Cross-cutting rules

- Authors are canonical (post `.mailmap` + manual merges) before any
  per-author metric is computed.
- Filters apply everywhere: repository, author, path prefix, time period
  (`since` inclusive / `until` exclusive), explicit commit list.
- Test repositories for correctness: **cJSON** (~1k commits), **Redis**
  (~13k), **git** (~75k); graders sample metrics at specific commit hashes.
