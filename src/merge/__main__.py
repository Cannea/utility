from .common import copy_chart_folder
from .helm_hander import consolidated_helm_chart_data, dump_consolidated_data_to_helm_chart
from .cli import parse_args
import sys
import logging

EXCLUDE_FILES = (
    "Chart.yaml",
    "dockerimages-values.yaml",
    "documentum-resources-values-extra-large.yaml",
    "documentum-resources-values-large.yaml",
    "documentum-resources-values-medium.yaml",
    "documentum-resources-values-medium-large.yaml",
    "documentum-resources-values-small.yaml",
    "documentum-resources-values-small-medium.yaml",
    "documentum-resources-values-test-small.yaml",
    "./config/passwords_k8api.yaml"
    "./config/passwords_vault.yaml"
    "./config/vault_secret.yaml"
)
EXCLUDE_DIRS = ("templates", "charts", "mergeUtility", "addons", "platforms", ".editor-config")
INCLUDE_DIRS = ("platforms")
INCLUDE_FILES = ("aws.yaml")

HELM_READ_CONFIG = {"exclude_dirs": EXCLUDE_DIRS, "exclude_files": EXCLUDE_FILES, "include_files": INCLUDE_FILES, "include_dirs": INCLUDE_DIRS}


def main():
    logging.basicConfig(filename="yaml_update.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    args = parse_args(sys.argv[1:])

    print("Parsed arguments:")
    for arg, value in vars(args).items():
        print(f"  {arg}: {value}")

    target_path = args.target_path

    if args.output:
        target_path = copy_chart_folder(target_path)

    app_version, processed_data = consolidated_helm_chart_data(chart_path=args.source_path, **HELM_READ_CONFIG)
    dump_consolidated_data_to_helm_chart(processed_data, chart_path=target_path, **HELM_READ_CONFIG)


if __name__ == "__main__":
    main()
