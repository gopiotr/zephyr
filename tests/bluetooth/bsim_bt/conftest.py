import pytest
import os
import sys
from pathlib import Path
import yaml
import copy

DEVICES_CONFIG_FILE_NAME_BASE = "devices_config"
DEVICES_CONFIG_FILE_EXTENSIONS = [".yaml", ".yml"]


@pytest.hookimpl(trylast=True)
def pytest_generate_tests(metafunc):
    if "devices_config" in metafunc.fixturenames:
        test_name = metafunc.definition.name
        test_dir_path = Path(metafunc.definition.fspath.dirname)
        devices_config_paths = _get_devices_config_paths(test_dir_path)
        if devices_config_paths:
            for devices_config_path in devices_config_paths:
                devices_config, config_ids = _load_configs(test_name, devices_config_path)
                metafunc.parametrize("devices_config", devices_config, ids=config_ids)
        else:
            print(f"Missing devices config file in folder {str(test_dir_path)}")
        pass


def _get_devices_config_paths(test_dir_path):
    devices_config_paths = []
    for obj in test_dir_path.iterdir():
        if obj.is_file() and \
                obj.name.startswith(DEVICES_CONFIG_FILE_NAME_BASE) and \
                obj.suffix in DEVICES_CONFIG_FILE_EXTENSIONS:
            devices_config_paths.append(obj)
    return devices_config_paths


def _load_configs(test_name, devices_config_path):
    devices_config = []
    config_ids = []

    yaml_configs: dict = yaml.safe_load(devices_config_path.open())
    if yaml_configs.get("configurations") is None:
        return devices_config, config_ids

    common = yaml_configs.get("common", {})

    for conf_name, config in yaml_configs["configurations"].items():

        for key, common_value in common.items():
            if key not in config:
                config[key] = copy.deepcopy(common_value)
            elif key == "devices":
                config[key] = _merge_common_device_options(common_value, config[key])
            elif key == "phy":
                config[key] = _merge_common_options(common_value, config[key])
            else:
                config = _merge_common_option(key, common_value, config)

        config_test_names = config.get("test_names", [])
        if config_test_names:
            if test_name not in config_test_names:
                continue

        devices_config.append(config)
        config_ids.append(conf_name)

    return devices_config, config_ids


def _merge_common_device_options(common_devices, config_devices_old):
    config_devices = copy.deepcopy(config_devices_old)
    for common_device_name, common_device_options in common_devices.items():
        device_found_flag = False
        for config_device_name, config_device_options in config_devices.items():
            if common_device_name == config_device_name:
                device_found_flag = True
                options_merged = _merge_common_options(common_device_options, config_device_options)
                config_devices[config_device_name] = options_merged
        if not device_found_flag:
            config_devices[common_device_name] = copy.deepcopy(common_device_options)
    return config_devices


def _merge_common_options(common_options, config_options_old):
    config_options = copy.deepcopy(config_options_old)
    for common_key, common_value in common_options.items():
        config_options = _merge_common_option(common_key, common_value, config_options)
    return config_options


def _merge_common_option(common_key, common_value, config_options_old):
    config_options = copy.deepcopy(config_options_old)
    if common_key not in config_options:
        config_options[common_key] = copy.deepcopy(common_value)
    elif isinstance(common_value, list):
        config_options[common_key] = config_options[common_key] + common_value
    elif isinstance(common_value, str):
        config_options[common_key] = f"{common_value} {config_options[common_key]}"
    else:
        pass
    return config_options


def get_env_var():
    env_var = {
        "ZEPHYR_BASE": os.getenv("ZEPHYR_BASE"),
        "BSIM_OUT_PATH": os.getenv("BSIM_OUT_PATH"),
        "BSIM_COMPONENTS_PATH": os.getenv("BSIM_COMPONENTS_PATH"),
    }

    exit_program_flag = False
    for var_name, var_value in env_var.items():
        if var_value is None:
            print(f'Please set "{var_name}" variable.')
            exit_program_flag = True

    if exit_program_flag:
        sys.exit()

    return env_var


@pytest.fixture(scope="module")
def env_var():
    return get_env_var()


class Parser():
    def parse(self, output):
        pass


@pytest.fixture()
def parser():
    return Parser()
