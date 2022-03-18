import os
import sys
import stat
import subprocess
import shutil
import pytest

ZEPHYR_BASE = os.getenv("ZEPHYR_BASE")
if not ZEPHYR_BASE:
    sys.exit("$ZEPHYR_BASE environment variable undefined")

BSIM_OUT_PATH = os.getenv("BSIM_OUT_PATH")
if not BSIM_OUT_PATH:
    sys.exit("$BSIM_OUT_PATH environment variable undefined")


class BabbleSimBuild:
    build_dir = os.path.join(ZEPHYR_BASE, "build")
    board_root = ZEPHYR_BASE
    board = "nrf52_bsim"
    cmake_generator = "Ninja"
    default_conf_file_name = "prj.conf"
    extra_ninja_args = []
    bsim_bin_path = os.path.join(BSIM_OUT_PATH, "bin")

    def __init__(self, test_path, extra_build_args=None):
        self.test_path = test_path
        self.test_name = os.path.basename(test_path)
        self.extra_build_args = [] if extra_build_args is None else extra_build_args
        self.conf_file_name = self._get_conf_file_name()
        self.built_exe_path = ""

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
            self.extra_build_args += [f"{conf_file_option_name}{conf_file_name}"]
        return conf_file_name

    def _clean_build_folder(self):
        if os.path.exists(self.build_dir) and os.path.isdir(self.build_dir):
            shutil.rmtree(self.build_dir)

    def _run_cmake(self):
        # TODO: refactor this constant variables to be more customizable
        cmake_args = [
            f"-B{self.build_dir}",
            f"-S{self.test_path}",
            f"-G{self.cmake_generator}",
            f"-DBOARD_ROOT={self.board_root}",
            f"-DBOARD={self.board}",
        ]

        cmake_args += self.extra_build_args

        cmake_exe = shutil.which("cmake")
        cmake_cmd = [cmake_exe] + cmake_args

        # TODO: use logger
        # print(f"Run CMake with command:\n{cmake_cmd}")

        p = subprocess.Popen(
            cmake_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout_data, stderr_data = p.communicate()

        if p.returncode != 0:
            # TODO: use logger
            print(p.returncode)
            print(stdout_data)
            print(stderr_data)
            raise subprocess.CalledProcessError

    def _run_ninja(self):
        ninja_args = [
            f'-C{self.build_dir}',
        ]

        ninja_args += self.extra_ninja_args

        ninja_exe = shutil.which("ninja")
        ninja_cmd = [ninja_exe] + ninja_args

        p = subprocess.Popen(
            ninja_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout_data, stderr_data = p.communicate()

        if p.returncode != 0:
            # TODO: use logger
            print(p.returncode)
            print(stdout_data)
            print(stderr_data)
            raise subprocess.CalledProcessError

    def _copy_exe(self):
        conf_file_basename = os.path.splitext(self.conf_file_name)[0]
        dst_exe_name = f"bs_{self.board}_{self.test_name}_{conf_file_basename}"

        current_exe_path = os.path.join(self.build_dir, "zephyr", "zephyr.exe")
        dst_exe_path = os.path.join(self.bsim_bin_path, dst_exe_name)
        shutil.copyfile(current_exe_path, dst_exe_path)

        # TODO: check why after copying user cannot execute program and if is
        #  simpler method to give this access?
        st = os.stat(dst_exe_path)
        os.chmod(dst_exe_path, st.st_mode | stat.S_IEXEC)

        self.built_exe_path = dst_exe_path

    def build(self):
        self._clean_build_folder()
        self._run_cmake()
        self._run_ninja()
        self._copy_exe()
        return self.built_exe_path
