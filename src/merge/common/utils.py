import os
import shutil
import logging

def deep_merge(dest, src):
    for k, v in src.items():
        if k not in dest:
            dest[k] = v
        else:
            if isinstance(dest[k], dict) and isinstance(v, dict):
                deep_merge(dest[k], v)
            else:
                dest[k] = v
    return dest

def copy_chart_folder(source_path, destination_path=None):
    if not os.path.isdir(source_path):
        logging.error(f"Source path does not exist or is not a directory: {source_path}")
        raise FileNotFoundError(f"Source path does not exist or is not a directory: {source_path}")

    folder_name = os.path.basename(os.path.normpath(source_path))

    if destination_path is None:
        base_destination = os.path.dirname(source_path)
        logging.info(f"No destination provided. Using source folder location: {base_destination}")
    else:
        base_destination = destination_path
        logging.info(f"Destination provided: {base_destination}")

    os.makedirs(base_destination, exist_ok=True)

    # Create a unique folder name to avoid overwriting
    new_folder_path = os.path.join(base_destination, folder_name)
    counter = 1
    while os.path.exists(new_folder_path):
        logging.warning(f"Folder already exists: {new_folder_path}")
        new_folder_path = os.path.join(base_destination, f"{folder_name}_copy{counter}")
        logging.info(f"Trying new folder name: {new_folder_path}")
        counter += 1

    # Copy the folder
    try:
        shutil.copytree(source_path, new_folder_path)
        logging.info(f"Successfully copied '{source_path}' to '{new_folder_path}'")
    except Exception as e:
        logging.error(f"Failed to copy folder: {e}")
        raise

    return new_folder_path

