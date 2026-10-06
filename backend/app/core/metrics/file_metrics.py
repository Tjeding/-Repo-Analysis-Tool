"""Per-file metric calculators live here (category = MetricCategory.FILE).

Examples of the kind of metrics expected: size, churn, authorship per file —
see docs/metrics.md for the authoritative catalogue from the brief.

Template:

    from app.core.metrics.base import MetricCalculator, register_metric
    from app.models.schemas import MetricCategory

    class MyFileMetric(MetricCalculator):
        key = "my_file_metric"
        category = MetricCategory.FILE
        description = "…"

        def calculate(self, repo_path, filters):
            ...  # return one MetricReport per in-scope file

    register_metric(MyFileMetric())
"""

# TODO: implement the file metrics specified in the brief.
