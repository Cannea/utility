import os
import fnmatch
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def iter_yaml_files(base_path: str,
                    exclude_dirs=None, exclude_files=None,
                    include_dirs=None, include_files=None):
    """
    Yield YAML file paths under base_path based on filtering rules.

    All patterns (for exclude/include) are relative to base_path and use forward slashes.
    Includes override excludes.

    Args:
        base_path (str): Root directory to start searching from.
        exclude_dirs (list): Patterns for directories to exclude.
        exclude_files (list): Patterns for files to exclude.
        include_dirs (list): Patterns for directories to explicitly include.
        include_files (list): Patterns for files to explicitly include.
    """

    # Helper to normalize patterns consistently
    def normalize(patterns):
        return [p.strip("./").replace("\\", "/") for p in patterns or []]

    exclude_dirs = set(normalize(exclude_dirs))
    exclude_files = set(normalize(exclude_files))
    include_dirs = set(normalize(include_dirs))
    include_files = set(normalize(include_files))

    for root, dirs, files in os.walk(base_path):
        rel_root = os.path.relpath(root, base_path).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""

        # Filter subdirectories in-place (affects traversal)
        dirs[:] = [
            d for d in dirs
            if not (
                any(fnmatch.fnmatch(f"{rel_root}/{d}".lstrip("/"), pat) for pat in exclude_dirs)
                and not any(fnmatch.fnmatch(f"{rel_root}/{d}".lstrip("/"), pat) for pat in include_dirs)
            )
        ]

        # Skip current dir if excluded and not overridden by include
        if rel_root and any(fnmatch.fnmatch(rel_root, pat) for pat in exclude_dirs) and \
           not any(fnmatch.fnmatch(rel_root, pat) for pat in include_dirs):
            logger.debug(f"Skipping excluded dir: {rel_root}")
            continue

        for file in files:
            rel_file_path = f"{rel_root}/{file}".lstrip("/")
            full_file_path = os.path.join(root, file)

            if not file.endswith((".yaml", ".yml")):
                continue

            # Apply file exclusion
            if any(fnmatch.fnmatch(rel_file_path, pat) for pat in exclude_files) and \
               not any(fnmatch.fnmatch(rel_file_path, pat) for pat in include_files):
                logger.debug(f"Skipping excluded file: {rel_file_path}")
                continue

            yield full_file_path
