import os
from .validators import is_helm_chart
from ruamel.yaml import YAML
from ruamel.yaml import CommentedMap

yaml = YAML()
yaml.preserve_quotes = True


def load_chart_metadata(chart_path: str) -> dict:
    """Load Chart.yaml and return metadata dict."""
    chart_yaml = os.path.join(chart_path, "Chart.yaml")
    with open(chart_yaml, "r", encoding="utf-8") as f:
        meta = yaml.load(f) or {}
    if not isinstance(meta, dict) or "name" not in meta:
        raise ValueError(f"Invalid Chart.yaml in {chart_path}")
    return meta


def get_chart_components(chart_meta: dict, chart_path: str):
    """
    Get all components (dependencies) from Chart.yaml and charts/ dir.
    """
    components = []

    # Dependencies from Chart.yaml
    if "dependencies" in chart_meta and isinstance(chart_meta["dependencies"], list):
        for dep in chart_meta["dependencies"]:
            if isinstance(dep, dict) and "name" in dep:
                components.append(dep["name"])

    # Charts directory subcharts
    charts_dir = os.path.join(chart_path, "charts")
    if os.path.isdir(charts_dir):
        for item in os.listdir(charts_dir):
            item_path = os.path.join(charts_dir, item)
            if os.path.isdir(item_path) and is_helm_chart(item_path):
                components.append(item)

    return sorted(set(components))


def get_disabled_components(components: list, data: dict) -> list:
    """
    Return a list of top-level keys (components) that have `enabled: false`.
    """
    disabled = []
    for component in components:
        if (isinstance(data[component], dict) or isinstance(data[component], CommentedMap)) and not data[component].get("enabled", True):
            disabled.append(component)
    return disabled
