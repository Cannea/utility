import os
import fnmatch
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def iter_yaml_files(base_path: str, exclude_dirs=None, exclude_files=None, include_dirs=None, include_files=None):
    """
    Yield YAML file paths matching filters.
    Includes override excludes.
    """
    exclude_dirs = exclude_dirs or ()
    exclude_files = exclude_files or ()
    include_dirs = include_dirs or ()
    include_files = include_files or ()

    exclude_dirs = set(exclude_dirs) - set(include_dirs)
    exclude_files = set(exclude_files) - set(include_files)

    for root, dirs, files in os.walk(base_path):
        rel_root = os.path.relpath(root, base_path)

        # Normalize rel_root for top-level
        if rel_root == ".":
            rel_root = ""

        # Check directory exclusion/inclusion
        excluded_dir = any(fnmatch.fnmatch(rel_root, pat) for pat in exclude_dirs)

        # If excluded and not explicitly included, skip this dir
        if excluded_dir:
            logger.debug(f"Skipping dir (excluded): {rel_root}")
            dirs.clear()
            continue

        for file in files:
            if file == "Chart.yaml":
                continue

            rel_path = os.path.normpath(os.path.join(rel_root, file))

            # Check file exclusion/inclusion
            excluded_file = any(fnmatch.fnmatch(file, pat) for pat in exclude_files)

            # If excluded and not explicitly included, skip this file
            if excluded_file:
                logger.debug(f"Skipping file (excluded): {rel_path}")
                continue

            if file.endswith((".yaml", ".yml")):
                yield os.path.join(root, file)
