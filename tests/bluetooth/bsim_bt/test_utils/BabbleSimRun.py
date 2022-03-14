
import os
import subprocess
from multiprocessing import Pool
import shutil

BSIM_OUT_PATH = r"/home/redbeard/bsim"
ZEPHYR_BASE = r"/home/redbeard/zephyrproject/zephyr"

bs_log_dir_general_name = "bs_out"
bs_log_dir_general_path = os.path.join(ZEPHYR_BASE, bs_log_dir_general_name)

def run_process(process_cmd , process_name, bs_cwd, bs_log_dir_path):
    p = subprocess.Popen(process_cmd, cwd=bs_cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = p.communicate()

    out_file_name = f"{process_name}_out.log"
    out_file_path = os.path.join(bs_log_dir_path, out_file_name)
    with open(out_file_path, "wb") as file:
        file.write(stdout_data)

    err_file_name = f"{process_name}_err.log"
    err_file_path = os.path.join(bs_log_dir_path, err_file_name)
    with open(err_file_path, "wb") as file:
        file.write(stderr_data)

    if p.returncode != 0:
        # TODO: think about better error rising way
        raise subprocess.CalledProcessError

    return p.returncode


class BabbleSimRun():
    verbosity_level = 2
    bsim_bin_path = os.path.join(BSIM_OUT_PATH, "bin")
    exe_medium_name = "bs_2G4_phy_v1"
    sim_length = "60e6"

    def __init__(self, simulation_id):
        self.simulation_id = simulation_id
        self.bs_log_dir_path = os.path.join(bs_log_dir_general_path, simulation_id)

    def _prepare_cmd(self, exe_path_0, testid_0, exe_path_1, testid_1):
        run_app_0_args = [
            f'-v={self.verbosity_level}',
            f'-s={self.simulation_id}',
            f'-d=0',
            f'-testid={testid_0}'
        ]

        run_app_0_cmd = [exe_path_0] + run_app_0_args

        run_app_1_args = [
            f'-v={self.verbosity_level}',
            f'-s={self.simulation_id}',
            f'-d=1',
            f'-testid={testid_1}'
        ]

        run_app_1_cmd = [exe_path_1] + run_app_1_args

        run_medium_args = [
            f'-v={self.verbosity_level}',
            f'-s={self.simulation_id}',
            f'-D=2',
            f'-sim_length={self.sim_length}'
        ]

        exe_medium_path = os.path.join(self.bsim_bin_path, self.exe_medium_name)

        run_medium_cmd = [exe_medium_path] + run_medium_args

        return run_app_0_cmd, run_app_1_cmd, run_medium_cmd

    def _clean_log_directory(self):
        # TODO: do not clean log directory but move them to "historical" folder
        if os.path.exists(self.bs_log_dir_path) and os.path.isdir(self.bs_log_dir_path):
            shutil.rmtree(self.bs_log_dir_path)
        os.makedirs(self.bs_log_dir_path, exist_ok=True)

    def run(self, exe_path_0, testid_0, exe_path_1, testid_1):
        run_app_0_cmd, run_app_1_cmd, run_medium_cmd = \
            self._prepare_cmd(exe_path_0, testid_0, exe_path_1, testid_1)

        # TODO: do not clean log directory but move them to "historical" folder
        self._clean_log_directory()

        run_app_0_pool_args = [run_app_0_cmd, f"{self.simulation_id}_{testid_0}", self.bsim_bin_path, self.bs_log_dir_path]
        run_app_1_pool_args = [run_app_1_cmd, f"{self.simulation_id}_{testid_1}", self.bsim_bin_path, self.bs_log_dir_path]
        run_medium_pool_args = [run_medium_cmd, f"{self.simulation_id}_medium", self.bsim_bin_path, self.bs_log_dir_path]
        pool = Pool(processes=3)
        run_app_0_result = pool.apply_async(run_process, run_app_0_pool_args)
        run_app_1_result = pool.apply_async(run_process, run_app_1_pool_args)
        run_medium_result = pool.apply_async(run_process, run_medium_pool_args)

        pool.close()
        pool.join()

        if run_app_0_result.get() != 0 or run_app_1_result.get() != 0 or run_medium_result.get() != 0:
            # TODO: use logger
            print(run_app_0_result.get())
            print(run_app_1_result.get())
            print(run_medium_result.get())
