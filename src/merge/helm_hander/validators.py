import os


def is_helm_chart(path: str) -> bool:
    """Check if the given path is a valid Helm chart."""
    chart_yaml = os.path.join(path, "Chart.yaml")
    return os.path.isfile(chart_yaml)