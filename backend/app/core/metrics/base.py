"""Extension point for all metric calculators.

To add a new metric, subclass `MetricCalculator` in the matching category
module (file_metrics.py, directory_metrics.py, repository_metrics.py,
commit_set_metrics.py) and register the instance with `register_metric`.
The API layer discovers registered calculators automatically — no route
changes are needed.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from app.models.schemas import MetricCategory, MetricFilter, MetricReport


class MetricCalculator(ABC):
    """Computes one metric over the scopes matching a MetricFilter.

    Attributes:
        key: stable identifier used in API payloads (e.g. "loc", "churn").
        category: which of the four metric categories this belongs to.
        description: human-readable summary shown in the dashboard.
    """

    key: str
    category: MetricCategory
    description: str = ""

    @abstractmethod
    def calculate(self, repo_path: Path, filters: MetricFilter) -> list[MetricReport]:
        """Compute this metric for every in-scope target of the repository
        at `repo_path`, honouring author/path/time/commit-list filters."""
        raise NotImplementedError


_REGISTRY: dict[str, MetricCalculator] = {}


def register_metric(calculator: MetricCalculator) -> MetricCalculator:
    """Add a calculator to the registry (call once per metric, at import)."""
    if calculator.key in _REGISTRY:
        raise ValueError(f"Duplicate metric key: {calculator.key}")
    _REGISTRY[calculator.key] = calculator
    return calculator


def get_metric(key: str) -> MetricCalculator:
    return _REGISTRY[key]


def list_metrics(category: MetricCategory | None = None) -> list[MetricCalculator]:
    """All registered calculators, optionally narrowed to one category."""
    calculators = list(_REGISTRY.values())
    if category is None:
        return calculators
    return [c for c in calculators if c.category is category]
