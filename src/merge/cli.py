import argparse
import os
import re
import sys


# -------------------- Validators --------------------
def is_yaml_file(path):
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"{path} is not a valid file.")
    if not path.endswith((".yaml", ".yml")):
        raise argparse.ArgumentTypeError(f"{path} is not a YAML file.")
    return path


def is_helm_folder(path):
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"{path} is not a valid folder.")
    if not os.path.exists(os.path.join(path, "Chart.yaml")):
        raise argparse.ArgumentTypeError("Missing 'Chart.yaml'. Not a Helm chart.")
    if not os.path.isdir(os.path.join(path, "templates")):
        raise argparse.ArgumentTypeError("Missing 'templates' directory. Not a Helm chart.")
    return path


def is_folder(path):
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"{path} is not a valid folder.")
    return path


def key_mapping(value):
    pattern = r"^\s*[^:]+:\s*[^:\s]*\s*$"
    if not re.match(pattern, value):
        raise argparse.ArgumentTypeError("Invalid format. Use 'source_key:target_key'")
    src, tgt = value.split(":", 1)
    return src.strip(), tgt.strip()


# -------------------- Main Parser --------------------
def parse_args(args):
    parser = argparse.ArgumentParser(prog="merge", description="Merge Utility CLI")
    parser.add_argument("--version", action="version", version="merge 25.4.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -------------------- File Subcommand --------------------
    file_parser = subparsers.add_parser("file", help="Merge/compare YAML files")
    file_parser.add_argument("source_path", type=is_yaml_file, help="Source YAML file path")
    file_parser.add_argument("target_path", type=is_yaml_file, help="Target YAML file path")

    # Common flags
    file_parser.add_argument("--compare-folder", type=is_folder, metavar="", help="Folder for compare report")
    file_parser.add_argument("--compare-only", action="store_true", help="Only perform compare")
    file_parser.add_argument("--compare", "-c", action="store_true", help="Enable compare before merging")
    file_parser.add_argument("--updated-key", metavar="", nargs="+", type=key_mapping, help="Custom key mappings: source:target")
    file_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    file_parser.add_argument("--log-folder", metavar="", type=is_folder, help="Folder for log reports")
    file_parser.add_argument("--output", "-o", action="store_true", help="Save updated target separately")

    # -------------------- Folder Subcommand --------------------
    folder_parser = subparsers.add_parser("folder", help="Merge/compare Helm chart folders")
    folder_parser.add_argument("source_path", type=is_helm_folder, help="Source Helm chart folder")
    folder_parser.add_argument("target_path", type=is_helm_folder, help="Target Helm chart folder")

    # Folder yes options (mutually exclusive)
    yes_group = folder_parser.add_mutually_exclusive_group()
    yes_group.add_argument("-Y", "--yes-all", action="store_true", help="Yes to all")
    yes_group.add_argument("-C", "--compare-all", action="store_true", help="Compare all files")
    yes_group.add_argument("-M", "--merge-all", action="store_true", help="Merge all files")

    # Common flags again
    folder_parser.add_argument("--compare-folder", type=is_folder, metavar="", help="Folder for compare report")
    folder_parser.add_argument("--compare-only", action="store_true", help="Only perform compare")
    folder_parser.add_argument("--compare", "-c", action="store_true", help="Enable compare before merging")
    folder_parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    folder_parser.add_argument("--log-folder", metavar="", type=is_folder, help="Folder for log reports")
    folder_parser.add_argument("--output", "-o", action="store_true", help="Save updated target separately")

    # Folder customization group
    folder_parser.add_argument("--updated-key", metavar="", nargs="+", type=key_mapping, help="Custom key mappings")
    folder_parser.add_argument("--updated-filename", metavar="", nargs="+", type=key_mapping, help="Custom filename mapping")
    folder_parser.add_argument("--configuration", metavar="", nargs="+", help="Additional config files in order")
    folder_parser.add_argument("--resource-file", metavar="", nargs="+", help="Target resource file(s)")
    folder_parser.add_argument("--platform", metavar="", nargs="+", help="Platform file(s)")
    folder_parser.add_argument("--otds-config", action="store_true", help="Merge OTDS bootstrap config")
    folder_parser.add_argument("--merge-disabled-components", action="store_true", help="Merge disabled components")

    # -------------------- Parse --------------------
    return parser.parse_args(args)
