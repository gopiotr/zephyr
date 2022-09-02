# Copyright (c) 2022 Nordic Semiconductor
#
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import yaml
import re
import csv

ZEPHYR_BASE_PATH = os.getenv("ZEPHYR_BASE")
if not ZEPHYR_BASE_PATH:
    print("Please set ZEPHYR_BASE environment variable")
    sys.exit(1)

SAMPLE_YAML_NAME = "sample.yaml"
TESTCASE_YAML_NAME = "testcase.yaml"

SHOW_WARNING = True


def show_warning(warning_text):
    if SHOW_WARNING:
        print(f"WARNING - {warning_text}")


options_dict_pattern = {
    "test_path": "",
    "testscenario_name": "",
    "tags": "",
    "type": "",
    "extra_args": "",
    "extra_configs": "",
    "build_only": "",
    "build_on_all": "",
    "skip": "",
    "slow": "",
    "timeout": "",
    "min_ram": "",
    "modules": "",
    "depends_on": "",
    "min_flash": "",
    "arch_allow": "",
    "arch_exclude": "",
    "extra_sections": "",
    "integration_platforms": "",
    "testcases": "",
    "platform_type": "",
    "platform_exclude": "",
    "platform_allow": "",
    "toolchain_exclude": "",
    "toolchain_allow": "",
    "filter": "",
    "harness": "",
    "harness_config": "",
    "seed": "",
}

testscenarios_options = []


def get_short_test_path(file_path):
    pattern = r"(?P<test_path_short>.+)/.+\.yaml"
    pattern = f"{ZEPHYR_BASE_PATH}/{pattern}"
    pattern = pattern.replace("/", "\\/")
    result = re.searchresult = re.search(pattern, file_path)
    test_path_short = result.group("test_path_short")
    return test_path_short


def option_name_valid(test_path_short, testscenario_name, option_name):
    if option_name in options_dict_pattern.keys():
        return True
    else:
        show_warning(f'Invalid option name "{option_name}" in {test_path_short}/{testscenario_name}')
        return False


def analyze_testscenario_options(file_path, testscenario_name, testscenario_options, common_options):
    global testscenarios_options
    options_dict = options_dict_pattern.copy()

    test_path_short = get_short_test_path(file_path)

    options_dict["test_path"] = test_path_short
    options_dict["testscenario_name"] = testscenario_name

    if common_options is not None:
        for option_name, option_value in common_options.items():
            if not option_name_valid(test_path_short, testscenario_name, option_name):
                continue
            options_dict[option_name] = option_value

    for option_name, option_value in testscenario_options.items():
        if not option_name_valid(test_path_short, testscenario_name, option_name):
            continue
        if isinstance(option_value, str) and options_dict[option_name] != "":
            # By default, we just concatenate string values of keys
            # which appear both in "common" and per-test sections,
            # but some keys are handled in adhoc way based on their
            # semantics.
            if option_name == "filter":
                options_dict[option_name] = f"({options_dict[option_name]}) and ({option_value})"
            else:
                options_dict[option_name] += f" {option_value}"
        else:
            options_dict[option_name] = option_value

    testscenarios_options.append(options_dict)


def parse_yaml_file(file_path, yaml_data):
    if "common" in yaml_data:
        common_options = yaml_data["common"]
    else:
        common_options = None

    if "tests" in yaml_data:
        for testscenario_name, testscenario_options in yaml_data["tests"].items():
            analyze_testscenario_options(file_path, testscenario_name, testscenario_options, common_options)
    else:
        show_warning(f"yaml without tests: {file_path}")


def open_yaml_file(file_path):
    with open(file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)
        parse_yaml_file(file_path, yaml_data)


def apply_filter():
    global testscenarios_options
    testscenarios_options_filtered = []

    for options_dict in testscenarios_options:
        # Iterate through all collected testscenarios and remove some of them,
        # which do not fill some conditions. For example if testscenarios with
        # "net" tag should be removed from scope, filtration could looks like:

        # if "net" in options_dict["tags"]:
        #     show_warning(f"Remove: {options_dict['test_path']}/{options_dict['testscenario_name']}")
        #     continue

        testscenarios_options_filtered.append(options_dict)

    testscenarios_options = testscenarios_options_filtered.copy()


def save_to_csv():
    global testscenarios_options
    # convert to string and add quotes
    for options_dict in testscenarios_options:
        for option_name in options_dict.keys():
            options_dict[option_name] = str(options_dict[option_name])

    # sort alphabetically by test path
    testscenarios_options = sorted(testscenarios_options, key=lambda op: op['test_path'])

    keys = options_dict_pattern.keys()
    csv_file_name = 'testscenarios_options.csv'
    with open(csv_file_name, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(testscenarios_options)
    print(f"Analysis saved into {csv_file_name}")


def main():
    root_folder_paths = [
        f"{ZEPHYR_BASE_PATH}/samples",
        f"{ZEPHYR_BASE_PATH}/tests"
    ]

    for root_folder_path in root_folder_paths:
        for subdir_path, dir_names, file_names in os.walk(root_folder_path):
            for file_name in file_names:
                if (file_name == SAMPLE_YAML_NAME) or (file_name == TESTCASE_YAML_NAME):
                    test_file_path = os.path.join(subdir_path, file_name)
                    open_yaml_file(test_file_path)
    apply_filter()
    save_to_csv()


if __name__ == "__main__":
    main()
