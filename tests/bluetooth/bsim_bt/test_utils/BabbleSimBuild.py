import logging
import os
import sys
import stat
import subprocess
import shutil
import json
import time
from filelock import FileLock

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


class BabbleSimBuild:
    build_timeout_duration = 300.0  # [s]
    board_root = ZEPHYR_BASE
    cmake_generator = "Ninja"
    board = "nrf52_bsim"
    default_conf_file_name = "prj.conf"
    extra_ninja_args = []

    def __init__(self, test_src_path, test_out_path, build_info_file_path,
                 general_exe_name, extra_build_args=None):
        self.test_src_path = test_src_path
        self.build_dir = os.path.join(test_out_path, "build")
        self.build_info_file_path = build_info_file_path

        if extra_build_args is None:
            self.extra_build_args = []
        else:
            self.extra_build_args = extra_build_args

        self.conf_file_name = self._get_conf_file_name()

        self.general_exe_name = general_exe_name
        self.general_exe_path = \
            os.path.join(BSIM_BIN_DIR_PATH, general_exe_name)

    def _get_conf_file_name(self):
        """
        Get conf file name from extra arguments, or if it not exists,
        add to extra args "-DCONF_FILE=" entry with default conf file name.
        """
        conf_file_option_name = "-DCONF_FILE="
        for extra_build_arg in self.extra_build_args:
            if extra_build_arg.startswith(conf_file_option_name):
                conf_file_name = extra_build_arg.split("=")[-1]
                break
        else:
            conf_file_name = self.default_conf_file_name
            self.extra_build_args += \
                [f"{conf_file_option_name}{conf_file_name}"]
        return conf_file_name

    def _clean_build_folder(self):
        if os.path.exists(self.build_dir) and os.path.isdir(self.build_dir):
            shutil.rmtree(self.build_dir)
        os.mkdir(self.build_dir)

    def _check_build_status(self):
        """
        TODO: write doc string
        """
        # TODO: refactor this method to simplify it
        lock = FileLock(f"{self.build_info_file_path}.lock")
        already_built_flag = False
        build_status = BuildStatus.in_progress
        timeout_lock = 120.0  # [s]
        wait_for_build_duration = 1.0  # [s]
        build_timeout = time.time() + self.build_timeout_duration

        while build_status == BuildStatus.in_progress:
            # TODO: add timeout
            with lock.acquire(timeout=timeout_lock):
                with open(self.build_info_file_path, "r") as file:
                    builds_info = json.load(file)
                build_info = builds_info.get(self.general_exe_name, {})
                build_status = build_info.get("status", BuildStatus.unknown)
                if build_status == BuildStatus.unknown:
                    builds_info[self.general_exe_name] = {
                        "status": BuildStatus.in_progress,
                        "build_path": self.build_dir
                    }
                    with open(self.build_info_file_path, "w") as file:
                        json.dump(builds_info, file, indent=4)
                    already_built_flag = False
                    break
                elif build_status == BuildStatus.finished:
                    build_path = build_info["build_path"]
                    log_msg = f"Used already existed build from: \n{build_path}"
                    logger.info(log_msg)
                    build_log_file_name = "build.log"
                    build_log_file_path = os.path.join(self.build_dir, build_log_file_name)
                    with open(build_log_file_path, "w") as file:
                        file.write(log_msg)
                    already_built_flag = True
                    break
            time.sleep(wait_for_build_duration)
            if time.time() > build_timeout:
                logger.error("Wait for build timeout.")
                raise TimeoutError

        return already_built_flag

    def _update_build_status(self):
        lock = FileLock(f"{self.build_info_file_path}.lock")
        with lock:
            with open(self.build_info_file_path, "r") as file:
                build_info = json.load(file)
            build_info[self.general_exe_name]["status"] = BuildStatus.finished
            with open(self.build_info_file_path, "w") as file:
                json.dump(build_info, file, indent=4)

    def _run_cmake(self):
        cmake_args = [
            f"-B{self.build_dir}",
            f"-S{self.test_src_path}",
            f"-G{self.cmake_generator}",
            f"-DBOARD_ROOT={self.board_root}",
            f"-DBOARD={self.board}",
        ]

        cmake_args += self.extra_build_args

        cmake_exe = shutil.which("cmake")
        cmake_cmd = [cmake_exe] + cmake_args

        cmake_cmd_log = " ".join(cmake_cmd)
        logger.info("Run CMake with command: \n%s", cmake_cmd_log)

        result = subprocess.run(
            cmake_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.build_timeout_duration
        )

        self._save_logs("cmake", result.stdout, result.stderr)

        if result.returncode != 0:
            logger.error("CMake error \nstdout_data: \n%s \nstderr_data: \n%s",
                         result.stdout, result.stderr)
            raise subprocess.CalledProcessError

    def _run_ninja(self):
        ninja_args = [
            f'-C{self.build_dir}',
        ]

        ninja_args += self.extra_ninja_args

        ninja_exe = shutil.which("ninja")
        ninja_cmd = [ninja_exe] + ninja_args

        ninja_cmd_log = " ".join(ninja_cmd)
        logger.info("Run Ninja with command: \n%s", ninja_cmd_log)

        result = subprocess.run(
            ninja_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.build_timeout_duration
        )

        self._save_logs("ninja", result.stdout, result.stderr)

        if result.returncode != 0:
            logger.error("Ninja error \nstdout_data: \n%s \nstderr_data: \n%s",
                         result.stdout, result.stderr)
            raise subprocess.CalledProcessError

    def _copy_exe(self):
        current_exe_path = os.path.join(self.build_dir, "zephyr", "zephyr.exe")

        dst_exe_path = self.general_exe_path

        logger.info("Copy exe file: \nsrc: %s \ndst: %s",
                    current_exe_path, dst_exe_path)

        shutil.copyfile(current_exe_path, dst_exe_path)

        # TODO: check why after copying user cannot execute program and if is
        #  simpler method to give this access?
        st = os.stat(dst_exe_path)
        os.chmod(dst_exe_path, st.st_mode | stat.S_IEXEC)

    def _save_logs(self, base_file_name, stdout_data, stderr_data):
        all_log_file_paths = ""

        out_file_name = f"{base_file_name}_out.log"
        out_file_path = os.path.join(self.build_dir, out_file_name)
        with open(out_file_path, "wb") as file:
            file.write(stdout_data)
        all_log_file_paths += f"\n{out_file_path}"

        if stderr_data:
            err_file_name = f"{base_file_name}_err.log"
            err_file_path = os.path.join(self.build_dir, err_file_name)
            with open(err_file_path, "wb") as file:
                file.write(stderr_data)
            all_log_file_paths += f"\n{err_file_path}"

        logger.info("Logs saved at: %s", all_log_file_paths)

    def build(self):
        self._clean_build_folder()
        already_built_flag = self._check_build_status()
        if already_built_flag:
            return
        self._run_cmake()
        self._run_ninja()
        self._copy_exe()
        self._update_build_status()


class BuildStatus:
    unknown = "unknown"
    in_progress = "in_progress"
    finished = "finished"
