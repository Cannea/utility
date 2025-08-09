import os
import fnmatch
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def iter_yaml_files(base_path: str, exclude_dirs=None, exclude_files=None,
                    include_dirs=None, include_files=None):
    """
    Yield YAML file paths matching filters.
    - exclude_dirs / exclude_files / include_dirs / include_files
      can be filename patterns or relative path patterns.
    - Paths are compared relative to base_path.
    - Excluded dirs are skipped entirely (no exceptions).
    """
    exclude_dirs = exclude_dirs or ()
    exclude_files = exclude_files or ()
    include_dirs = include_dirs or ()
    include_files = include_files or ()

    def norm_patterns(patterns):
        return [p.lstrip("./").replace("\\", "/") for p in patterns]

    exclude_dirs = set(norm_patterns(exclude_dirs))
    exclude_files = set(norm_patterns(exclude_files))
    include_dirs = set(norm_patterns(include_dirs))
    include_files = set(norm_patterns(include_files))

    for root, dirs, files in os.walk(base_path):
        rel_root = os.path.relpath(root, base_path).replace("\\", "/")
        if rel_root == ".":
            rel_root = ""

        # Remove all excluded subdirs, no exceptions
        dirs[:] = [
            d for d in dirs
            if not any(fnmatch.fnmatch(d, pat) or fnmatch.fnmatch(f"{rel_root}/{d}", pat)
                       for pat in exclude_dirs)
        ]

        # Process files
        for file in files:
            rel_path = os.path.normpath(os.path.join(rel_root, file)).replace("\\", "/")

            if any(fnmatch.fnmatch(rel_path, pat) for pat in exclude_files) \
               and not any(fnmatch.fnmatch(rel_path, pat) for pat in include_files):
                logger.debug(f"Skipping file (excluded): {rel_path}")
                continue

            if file.endswith((".yaml", ".yml")):
                yield os.path.join(root, file)
