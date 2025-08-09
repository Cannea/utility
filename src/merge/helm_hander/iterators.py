import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def iter_yaml_files(base_path: str,
                    exclude_dirs=None, exclude_files=None):

    exclude_dirs = set(exclude_dirs or [])
    exclude_files = set(exclude_files or [])

    for root, dirs, files in os.walk(base_path):
        # Filter out excluded directories in-place so os.walk skips them
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if not file.endswith((".yaml", ".yml")):
                continue

            if file in exclude_files:
                logger.debug(f"Skipping excluded file: {file}")
                continue

            yield os.path.join(root, file)
