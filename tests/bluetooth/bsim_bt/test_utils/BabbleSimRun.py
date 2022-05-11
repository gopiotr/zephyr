import logging
import os
import sys
import subprocess
import multiprocessing as mp
import abc

LOGGER_NAME = f"bsim_plugin.{__name__.split('.')[-1]}"
logger = logging.getLogger(LOGGER_NAME)

ZEPHYR_BASE = os.getenv("ZEPHYR_BASE")
if not ZEPHYR_BASE:
    sys.exit("$ZEPHYR_BASE environment variable undefined")

BSIM_OUT_PATH = os.getenv("BSIM_OUT_PATH")
if not BSIM_OUT_PATH:
    sys.exit("$BSIM_OUT_PATH environment variable undefined")

BSIM_BIN_DIR_NAME = "bin"
BSIM_BIN_DIR_PATH = os.path.join(BSIM_OUT_PATH, BSIM_BIN_DIR_NAME)

RUN_SIM_TIMEOUT_DURATION = 300.0  # [s]


class BabbleSimRun:
    def __init__(self, test_out_path, sim_id, general_exe_name, devices_config, medium_config):
        general_exe_path = os.path.join(BSIM_BIN_DIR_PATH, general_exe_name)
        self.devices = []
        for device_no, device_config in enumerate(devices_config):
            device = Device(sim_id, general_exe_path, device_no, device_config, test_out_path)
            self.devices.append(device)
        self.medium = Medium(sim_id, len(self.devices), medium_config, test_out_path)

    def run(self):
        self._log_run_bsim_cmd()

        if mp.get_start_method(allow_none=True) != "spawn":
            mp.set_start_method("spawn", force=True)

        number_processes = len(self.devices) + 1  # devices + medium
        pool = mp.Pool(processes=number_processes)

        for device in self.devices:
            device.run_process_result = \
                pool.apply_async(run_process, device.run_process_args)

        self.medium.run_process_result = \
            pool.apply_async(run_process, self.medium.run_process_args)

        pool.close()
        pool.join()

        self._log_run_bsim_info()

        self._verify_run_bsim_results()

    def _log_run_bsim_cmd(self):
        general_log_msg = "Run BabbleSim simulation with commands:"
        for device in self.devices:
            device_cmd_log = " ".join(device.process_cmd)
            general_log_msg += f"\n{device_cmd_log} &"

        medium_cmd_log = " ".join(self.medium.process_cmd)
        general_log_msg += f"\n{medium_cmd_log}"

        logger.info(general_log_msg)

    def _log_run_bsim_info(self):
        general_log_msg = f"Logs saved at:"

        for device in self.devices:
            general_log_msg += f"\n{device.log_file_base_path}_out.log"
            err_file_path = f"{device.log_file_base_path}_err.log"
            if os.path.exists(err_file_path):
                general_log_msg += f"\n{err_file_path}"

        general_log_msg += f"\n{self.medium.log_file_base_path}_out.log"
        err_file_path = f"{self.medium.log_file_base_path}_err.log"
        if os.path.exists(err_file_path):
            general_log_msg += f"\n{err_file_path}"

        logger.info(general_log_msg)

    def _verify_run_bsim_results(self):
        failure_occur_flag = False

        for device in self.devices:
            if device.run_process_result.get() != 0:
                logger.error("Failure during simulate %s device", device.name)
                failure_occur_flag = True

        if self.medium.run_process_result.get() != 0:
            logger.error("Failure during simulate %s medium", self.medium.name)
            failure_occur_flag = True

        assert failure_occur_flag is False


class BabbleSimObject(abc.ABC):
    def __init__(self, sim_id, name, exe_path, extra_run_args, test_out_path):
        self.sim_id = sim_id
        self.name = name
        self.exe_path = exe_path
        self.extra_run_args = extra_run_args
        self.log_file_base_path = os.path.join(test_out_path, name)
        self.process_cmd = self._get_cmd()
        self.run_process_args = self._prepare_run_process_args()
        self.run_process_result = None

    @abc.abstractmethod
    def _get_cmd(self):
        pass

    def _prepare_run_process_args(self):
        run_process_args = [
            self.process_cmd,
            self.log_file_base_path
        ]
        return run_process_args


class Device(BabbleSimObject):
    def __init__(self, sim_id, exe_path, device_no, device_config, test_out_path):
        name = device_config["id"]
        extra_run_args = device_config.get("extra_run_args", [])
        self.device_no = device_no

        super().__init__(sim_id, name, exe_path, extra_run_args, test_out_path)

    def _get_cmd(self):
        run_app_args = [
            f'-s={self.sim_id}',
            f'-d={self.device_no}',
            f'-testid={self.name}'
        ]
        run_app_args += self.extra_run_args
        run_app_cmd = [self.exe_path] + run_app_args
        return run_app_cmd


class Medium(BabbleSimObject):
    def __init__(self, sim_id, number_devices, medium_config, test_out_path):
        name = medium_config["name"]
        exe_medium_path = os.path.join(BSIM_BIN_DIR_PATH, name)
        extra_run_args = medium_config.get("extra_run_args", [])
        self.sim_length = medium_config["sim_length"]
        self.number_devices = number_devices

        super().__init__(sim_id, name, exe_medium_path, extra_run_args, test_out_path)

    def _get_cmd(self):
        run_medium_args = [
            f'-s={self.sim_id}',
            f'-D={self.number_devices}',
            f'-sim_length={self.sim_length}'
        ]
        run_medium_args += self.extra_run_args
        run_medium_cmd = [self.exe_path] + run_medium_args
        return run_medium_cmd


def run_process(process_cmd, log_file_base_path):
    ps_logger = ProcessLogger(log_file_base_path, debug_enable=False)

    result = subprocess.run(
        process_cmd,
        cwd=BSIM_BIN_DIR_PATH,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=RUN_SIM_TIMEOUT_DURATION
    )

    ps_logger.save_out_log(result.stdout)
    if result.stderr:
        ps_logger.save_err_log(result.stderr)

    return result.returncode


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
