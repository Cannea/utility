from .metadata import get_chart_components, load_chart_metadata, get_disabled_components
from .iterators import iter_yaml_files
from .processor import load_yaml_with_wrapped_scalars, load_yaml, update_yaml_from_wrapped_data
from .validators import is_helm_chart
from ..common.utils import deep_merge

import os
import logging
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def consolidated_helm_chart_data(
    chart_path: str, remove_disabled=False, values_order=None, exclude_dirs=None, exclude_files=None, include_dirs=None, include_files=None
):
    """
    Orchestrate Helm chart validation, metadata loading, YAML processing.
    """
    # Validate
    if not is_helm_chart(chart_path):
        raise ValueError(f"{chart_path} is not a valid Helm chart (missing Chart.yaml)")

    logger.info(f"Processing Helm chart: {chart_path}")

    # Load metadata
    meta = load_chart_metadata(chart_path)
    app_version = meta.get("appVersion")

    # Extract components
    components_list = get_chart_components(meta, chart_path)

    # Process YAML files
    processed_files = {}
    for yaml_file in iter_yaml_files(chart_path, exclude_dirs, exclude_files, include_dirs, include_files):
        try:
            data = load_yaml_with_wrapped_scalars(yaml_file)
            rel_path = os.path.relpath(yaml_file, chart_path)
            processed_files[rel_path] = data
            logger.debug(f"Processed file: {rel_path}")
        except Exception as e:
            logger.error(f"Error processing {yaml_file}: {e}", exc_info=True)

    processed_data = {}

    print(processed_files)

    if not values_order:
        for k, v in processed_files.items():
            processed_data = deep_merge(processed_data, v)
    else:
        for rel_path in values_order:
            print(rel_path)
            processed_data = (processed_data, processed_files.get(rel_path, {}))

    if remove_disabled:
        disabled_components = get_disabled_components(components_list, processed_data)
        processed_data = {key: val for key, val in processed_data.items() if key not in disabled_components}

    return app_version, processed_data

def dump_consolidated_data_to_helm_chart(wrapped_data, chart_path, exclude_dirs=None, exclude_files=None, include_dirs=None, include_files=None):
    for yaml_file in iter_yaml_files(chart_path, exclude_dirs, exclude_files, include_dirs, include_files):
        try:
            update_yaml_from_wrapped_data(wrapped_data, yaml_file, yaml_file)
            logger.debug(f"dumped to file: {yaml_file}")
        except Exception as e:
            logger.error(f"Error processing {yaml_file}: {e}", exc_info=True)

