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
    - Includes override excludes (even inside excluded dirs).
    - Excluded dirs are skipped unless they contain an explicitly included file.
    """
    exclude_dirs = exclude_dirs or ()
    exclude_files = exclude_files or ()
    include_dirs = include_dirs or ()
    include_files = include_files or ()

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

        # --- Handle excluded directories ---
        if any(fnmatch.fnmatch(os.path.basename(rel_root), pat) for pat in exclude_dirs) \
        and not any(fnmatch.fnmatch(rel_root, pat) for pat in include_dirs):
            
            has_included_file = any(
                fnmatch.fnmatch(f"{rel_root}/{f}", pat) for f in files for pat in include_files
            )

            if not has_included_file:
                logger.debug(f"Skipping dir (excluded): {rel_root}")
                dirs.clear()
                continue


        # --- Process files ---
        for file in files:
            rel_path = os.path.normpath(os.path.join(rel_root, file)).replace("\\", "/")

            if any(fnmatch.fnmatch(rel_path, pat) for pat in exclude_files) \
               and not any(fnmatch.fnmatch(rel_path, pat) for pat in include_files):
                logger.debug(f"Skipping file (excluded): {rel_path}")
                continue

            if file.endswith((".yaml", ".yml")):
                yield os.path.join(root, file)
