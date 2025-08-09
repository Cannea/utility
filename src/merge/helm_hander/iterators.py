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

    def normalize(patterns):
        return [p.replace("\\", "/").lstrip("/") for p in patterns or []]


    exclude_dirs = set(normalize(exclude_dirs))
    exclude_files = set(normalize(exclude_files))
    include_dirs = set(normalize(include_dirs))
    include_files = set(normalize(include_files))

    base_path = os.path.abspath(base_path)

    for root, dirs, files in os.walk(base_path):
        abs_root = os.path.abspath(root)
        rel_root = os.path.relpath(abs_root, base_path).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""

        # === EXCLUDE DIRECTORIES BEFORE DESCENDING ===
        pruned_dirs = []
        for d in dirs:
            rel_dir_path = f"{rel_root}/{d}".lstrip("/")
            if (
                any(fnmatch.fnmatch(rel_dir_path, pat) for pat in exclude_dirs)
                and not any(fnmatch.fnmatch(rel_dir_path, pat) for pat in include_dirs)
            ):
                logger.debug(f"Skipping excluded directory: {rel_dir_path}")
                continue
            pruned_dirs.append(d)
        dirs[:] = pruned_dirs  # In-place pruning

        # === PROCESS FILES ===
        for file in files:
            if not file.endswith((".yaml", ".yml")):
                continue

            rel_file_path = f"{rel_root}/{file}".lstrip("/")
            full_file_path = os.path.join(abs_root, file)

            if (
                any(fnmatch.fnmatch(rel_file_path, pat) for pat in exclude_files)
                and not any(fnmatch.fnmatch(rel_file_path, pat) for pat in include_files)
            ):
                logger.debug(f"Skipping excluded file: {rel_file_path}")
                continue

            yield full_file_path
