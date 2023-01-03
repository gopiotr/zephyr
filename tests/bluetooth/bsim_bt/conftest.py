import pytest
import os
import sys
from pathlib import Path
import yaml
import copy
import shutil
import logging

logger = logging.getLogger(__name__)

from twister2.device.native_simulator_adapter import NativeSimulatorAdapter


DEVICES_CONFIG_FILE_NAME = "devices_config.yaml"


@pytest.hookimpl(trylast=True)
def pytest_generate_tests(metafunc):
    if "devices_config" in metafunc.fixturenames:
        test_name = metafunc.definition.name
        test_dir_path = Path(metafunc.definition.fspath.dirname)
        devices_config_path = test_dir_path / DEVICES_CONFIG_FILE_NAME
        if devices_config_path.is_file():
            devices_config, config_ids = _load_configs(test_name, devices_config_path)
            metafunc.parametrize("devices_config", devices_config, ids=config_ids)
        else:
            print(f"Missing devices config file in folder {str(test_dir_path)}")
        pass


def _load_configs(test_name, devices_config_path):
    devices_config = []
    config_ids = []

    yaml_configs: dict = yaml.safe_load(devices_config_path.open())
    if yaml_configs.get("configurations") is None:
        return devices_config, config_ids

    for conf_name, config in yaml_configs["configurations"].items():
        config_test_names = config.get("test_names", [])
        if config_test_names and test_name not in config_test_names:
            continue

        devices_config.append(config)
        config_ids.append(conf_name)

    return devices_config, config_ids


@pytest.fixture()
def duts(request, devices_config):
    build_spec = request.session.specifications[request.node.nodeid]
    twister_config = request.config.twister_config
    duts = _generate_duts(request, twister_config, build_spec, devices_config)
    return duts


def _generate_duts(request, twister_config, build_spec, devices_config):
    platform_spec = twister_config.get_platform(build_spec.platform)
    if platform_spec.type == "native" and platform_spec.simulation == "native":
        duts = _generate_bsim_duts(request, build_spec, twister_config, devices_config)
    else:
        pytest.error("Tests dedicated only for BabbleSim simulator")
    return duts

def _generate_bsim_duts(request, build_spec, twister_config, devices_config):
    sim_id = _get_sim_id(request.node.name)
    exe_path = _copy_exe(build_spec.build_dir, sim_id)

    duts = {}
    device_idx = 0
    devices_number = len(devices_config["devices"]) - 1
    for device_name, device_config in devices_config["devices"].items():
        if device_name == "bsim_phy":
            duts[device_name] = _generate_bsim_phy(device_config, twister_config, sim_id, devices_number)
        else:
            duts[device_name] = _generate_bsim_device(device_config, exe_path, twister_config, sim_id, device_idx)
            device_idx += 1
    return duts


def _generate_bsim_phy(phy_config, twister_config, sim_id, devices_number):
    env_var = _get_env_var()
    phy_application_path = phy_config["application"]
    phy_application_path = phy_application_path.replace("${BSIM_OUT_PATH}", env_var["BSIM_OUT_PATH"])
    phy_command = [phy_application_path, f"-s={sim_id}", f"-D={devices_number}"] + phy_config.get("bsim_extra_args", [])
    phy = NativeSimulatorAdapter(twister_config)
    phy.command = phy_command
    phy.process_kwargs["cwd"] = str(Path(phy_application_path).parent)
    return phy


def _generate_bsim_device(device_config, exe_path, twister_config, sim_id, device_idx):
    device_command = [str(exe_path), f"-s={sim_id}", f"-d={device_idx}"] + device_config.get("bsim_extra_args", [])
    device = NativeSimulatorAdapter(twister_config)
    device.command = device_command
    device.process_kwargs["cwd"] = str(Path(exe_path).parent)
    return device


def _get_sim_id(test_name):
    sim_id = test_name
    sim_id = sim_id.replace("[", "_")
    sim_id = sim_id.replace("]", "")
    sim_id = sim_id.replace(".", "_")
    sim_id = sim_id.replace(":", "_")
    sim_id = sim_id.replace("-", "_")
    return sim_id


def _copy_exe(build_dir, sim_id):
    old_exe_path = build_dir / "zephyr" / "zephyr.exe"

    bsim_out_bin_path = Path(os.getenv("BSIM_OUT_PATH")) / "bin"
    new_exe_path = bsim_out_bin_path / sim_id

    shutil.copy(old_exe_path, new_exe_path)

    return new_exe_path


def _get_env_var():
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
