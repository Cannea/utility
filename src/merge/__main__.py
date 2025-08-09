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
    "passwords_k8api.yaml",
    "passwords_vault.yaml",
    "vault_secret.yaml",
)
EXCLUDE_DIRS_SOURCE = ("templates", "charts", "mergeUtility", ".editor-config")
EXCLUDE_DIRS_TARGET = ("templates", "charts", "mergeUtility", ".editor-config", "platforms")
INCLUDE_DIRS = ()
INCLUDE_FILES = ()

HELM_READ_CONFIG_SOURCE = {
    "exclude_dirs": EXCLUDE_DIRS_SOURCE,
    "exclude_files": EXCLUDE_FILES,
    "include_files": INCLUDE_FILES,
    "include_dirs": INCLUDE_DIRS,
}
HELM_READ_CONFIG_TARGET = {
    "exclude_dirs": EXCLUDE_DIRS_TARGET,
    "exclude_files": EXCLUDE_FILES,
    "include_files": INCLUDE_FILES,
    "include_dirs": INCLUDE_DIRS,
}

VALUES_ORDER_DEFAULT = [
    "./config/configuration.yml",
    "./config/constants.yaml",
    "./config/passwords.yaml",
    "./platforms/anthos.yaml",
    "./documentum-resources-values-dev-test.yaml",
    "./documentum-components.yaml",
]


def main():
    logging.basicConfig(filename="yaml_update.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    args = parse_args(sys.argv[1:])

    print("Parsed arguments:")
    for arg, value in vars(args).items():
        print(f"  {arg}: {value}")

    target_path = args.target_path
    values_order = args.configuration if args.configuration != None else VALUES_ORDER_DEFAULT
    print(f"values: {values_order}")

    if args.output:
        target_path = copy_chart_folder(target_path)

    app_version, processed_data = consolidated_helm_chart_data(chart_path=args.source_path, values_order=values_order, **HELM_READ_CONFIG_SOURCE)
    dump_consolidated_data_to_helm_chart(processed_data, chart_path=target_path, **HELM_READ_CONFIG_TARGET)


if __name__ == "__main__":
    main()
