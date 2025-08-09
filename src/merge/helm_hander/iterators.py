import os
import fnmatch
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def iter_yaml_files(base_path: str, exclude_dirs=None, exclude_files=None,
                    include_dirs=None, include_files=None):
    """
    Yield YAML file paths matching filters.
    
    Parameters:
        base_path (str): Base directory to search in.
        exclude_dirs (list): List of directory patterns to exclude (relative to base_path).
        exclude_files (list): List of file patterns to exclude (relative to base_path).
        include_dirs (list): List of directory patterns to include (overrides exclude_dirs).
        include_files (list): List of file patterns to include (overrides exclude_files).

    Yields:
        str: Absolute paths to YAML files matching the criteria.
    """
    exclude_dirs = exclude_dirs or []
    exclude_files = exclude_files or []
    include_dirs = include_dirs or []
    include_files = include_files or []

    def norm_patterns(patterns):
        return [p.lstrip("./").replace("\\", "/") for p in patterns]

    exclude_dirs = set(norm_patterns(exclude_dirs)) - set(norm_patterns(include_dirs))
    exclude_files = set(norm_patterns(exclude_files)) - set(norm_patterns(include_files))
    include_dirs = set(norm_patterns(include_dirs))
    include_files = set(norm_patterns(include_files))

    for root, dirs, files in os.walk(base_path):
        rel_root = os.path.relpath(root, base_path).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""

        # Filter out excluded subdirectories
        dirs[:] = [
            d for d in dirs
            if not (
                any(fnmatch.fnmatch(f"{rel_root}/{d}".lstrip("/"), pat) for pat in exclude_dirs)
                and not any(fnmatch.fnmatch(f"{rel_root}/{d}".lstrip("/"), pat) for pat in include_dirs)
            )
        ]

        # Skip current dir entirely if excluded and not explicitly included
        if any(fnmatch.fnmatch(rel_root, pat) for pat in exclude_dirs) and \
           not any(fnmatch.fnmatch(rel_root, pat) for pat in include_dirs):
            logger.debug(f"Skipping directory (excluded): {rel_root}")
            continue

        for file in files:
            rel_path = f"{rel_root}/{file}".lstrip("/")
            full_path = os.path.join(root, file)

            # Apply file exclusions
            if any(fnmatch.fnmatch(rel_path, pat) for pat in exclude_files) and \
               not any(fnmatch.fnmatch(rel_path, pat) for pat in include_files):
                logger.debug(f"Skipping file (excluded): {rel_path}")
                continue

            # Only yield YAML files
            if file.endswith((".yaml", ".yml")):
                logger.info(f"Yielding YAML file: {rel_path}")
                yield full_path
