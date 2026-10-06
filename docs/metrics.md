# RAT Metric Catalogue

Authoritative list of the metrics RAT computes, grouped by the four
categories from the brief. Every metric is implemented as a
`MetricCalculator` (see `backend/app/core/metrics/base.py`) and appears in
API responses as an entry in `MetricReport.metrics` keyed by its `key`.

> Fill in the "Definition" column from the course brief as each metric is
> implemented. Keys are stable identifiers used in API payloads.

## File Metrics

Scope: one `MetricReport` per in-scope file.

| Key | Metric | Definition | Unit |
| --- | ------ | ---------- | ---- |
| _tbd_ | _per brief_ | _per brief_ | _tbd_ |

## Directory Metrics

Scope: one `MetricReport` per in-scope directory (aggregated over contained
files).

| Key | Metric | Definition | Unit |
| --- | ------ | ---------- | ---- |
| _tbd_ | _per brief_ | _per brief_ | _tbd_ |

## Repository Metrics

Scope: a single `MetricReport` for the whole repository.

| Key | Metric | Definition | Unit |
| --- | ------ | ---------- | ---- |
| _tbd_ | _per brief_ | _per brief_ | _tbd_ |

## Commit Set Metrics

Scope: the set of commits selected by the filter — either a time period
(`since`/`until`) or a manually selected list of SHAs.

| Key | Metric | Definition | Unit |
| --- | ------ | ---------- | ---- |
| _tbd_ | _per brief_ | _per brief_ | _tbd_ |

## Cross-cutting rules

- **Authors** are always canonical (post `.mailmap` + manual merges) before
  any per-author breakdown is computed.
- **Filters** apply to every metric: repository, author, path prefix, time
  period, explicit commit list.
- New metrics must be registered via `register_metric(...)` in their
  category module — the API then exposes them automatically.
