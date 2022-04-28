import logging
import os
import sys
import subprocess
import multiprocessing as mp
import pytest

LOGGER_NAME = f"bsim_plugin.{__name__.split('.')[-1]}"
logger = logging.getLogger(LOGGER_NAME)

ZEPHYR_BASE = os.getenv("ZEPHYR_BASE")
if not ZEPHYR_BASE:
    sys.exit("$ZEPHYR_BASE environment variable undefined")

BSIM_OUT_PATH = os.getenv("BSIM_OUT_PATH")
if not BSIM_OUT_PATH:
    sys.exit("$BSIM_OUT_PATH environment variable undefined")


def run_process(process_cmd, bs_cwd, log_file_base_path):
    ps_logger = ProcessLogger(log_file_base_path, debug_enable=False)

    p = subprocess.Popen(
        process_cmd,
        cwd=bs_cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout_data, stderr_data = p.communicate()

    ps_logger.save_out_log(stdout_data)
    if stderr_data:
        ps_logger.save_err_log(stderr_data)

    return p.returncode


class BabbleSimRun:
    bsim_bin_path = os.path.join(BSIM_OUT_PATH, "bin")

    def __init__(self, test_out_path, sim_id, app_exe_path,
                 devices_config, medium_config):
        self.sim_id = sim_id
        self.test_out_path = test_out_path
        self.devices = self._define_devices(app_exe_path, devices_config)
        self.medium = Medium(self.bsim_bin_path, len(self.devices), medium_config, self.test_out_path)

    def _define_devices(self, app_exe_path, devices_config):
        devices = []
        for device_no, device_config in enumerate(devices_config):
            devices.append(Device(app_exe_path, device_no, device_config, self.test_out_path))
        return devices

    def run(self):
        run_apps_pool_args = self._get_apps_pool_args()
        run_medium_pool_args = self._get_medium_pool_args()

        self._log_run_bsim_cmd(run_apps_pool_args, run_medium_pool_args)

        if mp.get_start_method(allow_none=True) != "spawn":
            mp.set_start_method("spawn", force=True)

        number_processes = len(self.devices) + 1  # devices + medium
        pool = mp.Pool(processes=number_processes)

        run_app_results = []
        for run_app_pool_args in run_apps_pool_args:
            run_app_result = pool.apply_async(run_process, run_app_pool_args)
            run_app_results.append(run_app_result)

        run_medium_result = pool.apply_async(run_process, run_medium_pool_args)

        pool.close()
        pool.join()

        self._save_run_bsim_info_log()

        self._verify_run_bsim_results(run_app_results, run_medium_result)

    def _get_apps_pool_args(self):
        run_apps_pool_args = []
        for device in self.devices:
            run_app_pool_args = self._get_app_pool_args(device)
            run_apps_pool_args.append(run_app_pool_args)
        return run_apps_pool_args

    def _get_app_pool_args(self, device):
        process_cmd = device.get_cmd(self.sim_id)
        log_file_base_path = device.log_file_base_path
        run_app_pool_args = self._get_pool_args(process_cmd, log_file_base_path)
        return run_app_pool_args

    def _get_medium_pool_args(self):
        process_cmd = self.medium.get_cmd(self.sim_id)
        log_file_base_path = self.medium.log_file_base_path
        run_medium_pool_args = self._get_pool_args(process_cmd, log_file_base_path)
        return run_medium_pool_args

    def _get_pool_args(self, process_cmd, log_file_base_path):
        run_pool_args = [
            process_cmd,
            self.bsim_bin_path,
            log_file_base_path
        ]
        return run_pool_args

    @staticmethod
    def _log_run_bsim_cmd(run_apps_pool_args, run_medium_pool_args):
        device_cmd_logs = [" ".join(args[0]) for args in run_apps_pool_args]
        device_cmd_log = " &\n".join(device_cmd_logs)
        medium_cmd_log = " ".join(run_medium_pool_args[0])
        bsim_cmd_log = f"{device_cmd_log} &\n{medium_cmd_log}"
        logger.info("Run BabbleSim simulation with commands: \n%s",
                    bsim_cmd_log)

    def _save_run_bsim_info_log(self):
        general_log_msg = f"Logs saved at:"

        for device in self.devices:
            general_log_msg += f"\n{device.log_file_base_path}_*.log"

        general_log_msg += f"\n{self.medium.log_file_base_path}_*.log"
        
        logger.info(general_log_msg)

    def _verify_run_bsim_results(self, run_app_results, run_medium_result):
        fail_occur_flag = False

        for run_app_result in run_app_results:
            if run_app_result.get() != 0:
                fail_occur_flag = True

        if run_medium_result.get() != 0:
            fail_occur_flag = True

        if fail_occur_flag:
            logger.error("Some fail occur during run BabbleSim simulation.")

        assert fail_occur_flag == False


class Device:
    def __init__(self, exe_path, device_no, device_config, test_out_path):
        self.exe_path = exe_path
        self.device_no = device_no
        self.id = device_config["id"]
        self.extra_run_args = device_config.get("extra_run_args", [])
        self.log_file_base_path = os.path.join(test_out_path, self.id)

    def get_cmd(self, sim_id):
        run_app_args = [
            f'-s={sim_id}',
            f'-d={self.device_no}',
            f'-testid={self.id}'
        ]
        run_app_args += self.extra_run_args
        run_app_cmd = [self.exe_path] + run_app_args
        return run_app_cmd


class Medium:
    def __init__(self, bsim_bin_path, number_devices, medium_config, test_out_path):
        self.name = medium_config["name"]
        self.exe_medium_path = os.path.join(bsim_bin_path, self.name)
        self.sim_length = medium_config["sim_length"]
        self.number_devices = number_devices
        self.extra_run_args = medium_config.get("extra_run_args", [])
        self.log_file_base_path = os.path.join(test_out_path, self.name)

    def get_cmd(self, sim_id):
        run_medium_args = [
            f'-s={sim_id}',
            f'-D={self.number_devices}',
            f'-sim_length={self.sim_length}'
        ]
        run_medium_args += self.extra_run_args
        run_medium_cmd = [self.exe_medium_path] + run_medium_args
        return run_medium_cmd


class ProcessLogger:
    def __init__(self, log_file_base_path, debug_enable=False):
        self.out_file_path = f"{log_file_base_path}_out.log"

        self.err_file_path = f"{log_file_base_path}_err.log"

        self.debug_file_path = f"{log_file_base_path}_debug.log"
        self.debug_enable = debug_enable
        process_name = os.path.basename(log_file_base_path)
        self.save_debug_log(f"Debug logger for process: {process_name}, "
                            f"with PID: {os.getpid()}\n\n")

    def save_out_log(self, data):
        self._save_log(self.out_file_path, data)

    def save_err_log(self, data):
        self._save_log(self.err_file_path, data)

    @staticmethod
    def _save_log(log_file_path, data):
        with open(log_file_path, "wb") as file:
            file.write(data)

    def save_debug_log(self, log):
        if self.debug_enable:
            with open(self.debug_file_path, "a") as file:
                file.write(log)
