import os
import stat
import subprocess
import shutil

# TODO: use OS Path
ZEPHYR_BASE = r"/home/redbeard/zephyrproject/zephyr"
BSIM_OUT_PATH = r"/home/redbeard/bsim"

class BabbleSimBuild():
    # TODO: refactor this constant variables to be more customizable
    build_dir = os.path.join(ZEPHYR_BASE, "build")
    board_root = ZEPHYR_BASE
    board = "nrf52_bsim"
    conf_file = "prj.conf"
    conf_overlay = ""
    additional_cmake_args = [
        "-DCONFIG_COVERAGE=y",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
    ]
    cc_flags = '"-Werror"'

    additional_ninja_args = []

    bsim_bin_path = os.path.join(BSIM_OUT_PATH, "bin")

    def __init__(self, test_path) -> None:
        self.test_path = test_path
        self.test_name = os.path.basename(test_path)
        self.built_exe_path = ""

    def _clean_build_folder(self, ):
        if os.path.exists(self.build_dir) and os.path.isdir(self.build_dir):
            shutil.rmtree(self.build_dir)

    def _run_cmake(self):
        # TODO: refactor this constant variables to be more customizable
        cmake_args = [
            f'-B{self.build_dir}',
            f'-S{self.test_path}',
            f'-GNinja',
            f'-DBOARD_ROOT={self.board_root}',
            f'-DBOARD={self.board}',
            f'-DCONF_FILE={self.conf_file}',
            f'-DOVERLAY_CONFIG={self.conf_overlay}',
            f'-DCMAKE_C_FLAGS={self.cc_flags}',
        ]

        cmake_args += self.additional_cmake_args

        cmake_exe = shutil.which("cmake")
        cmake_cmd = [cmake_exe] + cmake_args

        p = subprocess.Popen(cmake_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = p.communicate()

        if p.returncode != 0:
            # TODO: use logger
            print(p.returncode)
            print(stdout_data)
            print(stderr_data)
            raise subprocess.CalledProcessError

    def _run_ninja(self):
        # TODO: refactor this constant variables to be more customizable
        ninja_args = [
            f'-C{self.build_dir}',
        ]

        ninja_args += self.additional_ninja_args

        ninja_exe = shutil.which("ninja")
        ninja_cmd = [ninja_exe] + ninja_args

        p = subprocess.Popen(ninja_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = p.communicate()

        if p.returncode != 0:
            # TODO: use logger
            print(p.returncode)
            print(stdout_data)
            print(stderr_data)
            raise subprocess.CalledProcessError

    def _copy_exe(self):
        conf_file_basename = os.path.splitext(self.conf_file)[0]
        dst_exe_name = f"bs_{self.board}_{self.test_name}_{conf_file_basename}"

        current_exe_path = os.path.join(self.build_dir, "zephyr", "zephyr.exe")
        dst_exe_path = os.path.join(self.bsim_bin_path, dst_exe_name)
        shutil.copyfile(current_exe_path, dst_exe_path)

        # TODO: check why after copying user cannot execute program and if is simpler method to give this access?
        st = os.stat(dst_exe_path)
        os.chmod(dst_exe_path, st.st_mode | stat.S_IEXEC)

        self.built_exe_path = dst_exe_path

    def build(self):
        self._clean_build_folder()
        self._run_cmake()
        self._run_ninja()
        self._copy_exe()
        return self.built_exe_path
