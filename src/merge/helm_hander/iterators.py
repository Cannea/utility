import os
import fnmatch
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def iter_yaml_files(base_path: str, exclude_dirs=None, exclude_files=None,
                    include_dirs=None, include_files=None):
    """
    Yield YAML file paths matching filters.
    Supports exclusion/inclusion of directories and files by pattern.
    """
    exclude_dirs = exclude_dirs or []
    exclude_files = exclude_files or []
    include_dirs = include_dirs or []
    include_files = include_files or []

    def norm_patterns(patterns):
        return [p.strip("./").replace("\\", "/") for p in patterns]

    # Normalize all patterns
    exclude_dirs = norm_patterns(exclude_dirs)
    exclude_files = norm_patterns(exclude_files)
    include_dirs = norm_patterns(include_dirs)
    include_files = norm_patterns(include_files)

    for root, dirs, files in os.walk(base_path):
        # Normalize relative path
        rel_root = os.path.relpath(root, base_path).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""

        # Filter subdirectories (in-place to affect os.walk)
        dirs[:] = [
            d for d in dirs
            if not (
                any(fnmatch.fnmatch(f"{rel_root}/{d}".lstrip("/"), pat) for pat in exclude_dirs)
                and not any(fnmatch.fnmatch(f"{rel_root}/{d}".lstrip("/"), pat) for pat in include_dirs)
            )
        ]

        # Check if the current directory itself is excluded
        if any(fnmatch.fnmatch(rel_root, pat) for pat in exclude_dirs) and \
           not any(fnmatch.fnmatch(rel_root, pat) for pat in include_dirs):
            logger.debug(f"Skipping directory (excluded): {rel_root}")
            continue

        for file in files:
            rel_path = f"{rel_root}/{file}".lstrip("/")
            full_path = os.path.join(root, file)

            # File exclusion logic
            if any(fnmatch.fnmatch(rel_path, pat) for pat in exclude_files) and \
               not any(fnmatch.fnmatch(rel_path, pat) for pat in include_files):
                logger.debug(f"Skipping file (excluded): {rel_path}")
                continue

            if file.endswith((".yaml", ".yml")):
                logger.debug(f"Yielding YAML file: {rel_path}")
                yield full_path
