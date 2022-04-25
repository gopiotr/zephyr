import os
import sys
import logging
import shutil
import pytest
from test_utils.TestcaseYamlParser import TestcaseYamlParser
from test_utils.BabbleSimBuild import BabbleSimBuild
from test_utils.BabbleSimRun import BabbleSimRun

LOGGER_NAME = "bsim_plugin"
logger = logging.getLogger(LOGGER_NAME)

ZEPHYR_BASE = os.getenv("ZEPHYR_BASE")
if not ZEPHYR_BASE:
    sys.exit("$ZEPHYR_BASE environment variable undefined")

BSIM_TESTS_OUT_DIR_NAME = "bsim_tests_out"
BSIM_TESTS_OUT_DIR_PATH = os.path.join(ZEPHYR_BASE, BSIM_TESTS_OUT_DIR_NAME)


def prepare_bsim_test_out_dir():
    # TODO: refactor this to simplify out dir preparation and write "smarter"
    #  detection of historical directories
    if os.path.exists(BSIM_TESTS_OUT_DIR_PATH):
        max_dir_number = 100
        for idx in range(1, max_dir_number):
            new_dir_path = f"{BSIM_TESTS_OUT_DIR_PATH}_{idx}"
            if not os.path.exists(new_dir_path):
                # Cannot use logger yet, so just use print
                print(f"Copy output directories: "
                      f"\nsrc: {BSIM_TESTS_OUT_DIR_PATH} "
                      f"\ndst: {new_dir_path}")
                shutil.move(BSIM_TESTS_OUT_DIR_PATH, new_dir_path)
                break
        else:
            err_msg = f'Too many historical directories. Remove some ' \
                      f'"{BSIM_TESTS_OUT_DIR_NAME}" folders.'
            logger.error(err_msg)
            sys.exit(err_msg)
    os.mkdir(BSIM_TESTS_OUT_DIR_PATH)


def setup_logger(config):
    is_worker_input = hasattr(config, 'workerinput')  # xdist worker
    if is_worker_input:
        worker_id = config.workerinput['workerid']
        log_file_name = f'bsim_test_plugin_{worker_id}.log'
    else:
        log_file_name = "bsim_test_plugin.log"
    log_file_path = os.path.join(BSIM_TESTS_OUT_DIR_PATH, log_file_name)
    file_handler = logging.FileHandler(log_file_path, mode="w")
    # TODO: remove extended log format
    # formatter_file = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #     datefmt="%H:%M:%S"
    # )
    formatter_file = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt="%H:%M:%S"
    )
    file_handler.setFormatter(formatter_file)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)


def pytest_configure(config):
    is_worker_input = hasattr(config, 'workerinput')  # xdist worker
    if not is_worker_input:
        prepare_bsim_test_out_dir()
    setup_logger(config)


def pytest_collect_file(parent, path):
    if path.basename.startswith("bs_testcase") and (path.ext == ".yaml" or path.ext == ".yml"):
        return YamlFile.from_parent(parent, fspath=path)


class YamlFile(pytest.File):
    def collect(self):
        test_src_path = self.fspath.dirpath()

        parser = TestcaseYamlParser()
        yaml_data = parser.load(self.fspath)
        testscenarios = yaml_data.get("tests", {})
        for testscenario_name, testscenario_config in testscenarios.items():
            if "bsim_config" not in testscenario_config:
                continue
            yield YamlItem.from_parent(
                self,
                test_src_path=test_src_path,
                testscenario_name=testscenario_name,
                testscenario_config=testscenario_config
            )


class YamlItem(pytest.Item):
    def __init__(self, parent, test_src_path, testscenario_name,
                 testscenario_config):
        super().__init__(testscenario_name, parent)

        logger.info("Found test scenario: %s", testscenario_name)

        self.test_src_path = test_src_path
        self.extra_build_args = testscenario_config.get("extra_args", [])

        self.sim_id = testscenario_name.replace(".", "_")
        self.test_out_path = os.path.join(BSIM_TESTS_OUT_DIR_PATH, self.sim_id)

        bsim_config = testscenario_config["bsim_config"]
        self.devices = bsim_config.get("devices", [])
        self.medium = bsim_config.get("medium", {})

    def runtest(self):
        logger.info("Start test: %s", self.name)

        os.makedirs(self.test_out_path)

        bs_builder = BabbleSimBuild(
            self.test_src_path,
            self.test_out_path,
            self.sim_id,
            extra_build_args=self.extra_build_args
        )
        exe_path = bs_builder.build()

        # # TODO: remove below mock (for test only)
        # BSIM_OUT_PATH = os.getenv("BSIM_OUT_PATH")
        # bsim_bin_path = os.path.join(BSIM_OUT_PATH, "bin")
        # exe_name = f"bs_nrf52_bsim_{self.sim_id}"
        # exe_path = os.path.join(bsim_bin_path, exe_name)

        bs_runner = BabbleSimRun(
            self.test_out_path,
            self.sim_id,
            exe_path,
            self.devices,
            self.medium
        )
        bs_runner.run()
        if False:
            raise YamlException(self)

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        if isinstance(excinfo.value, YamlException):
            return "Test fails"


class YamlException(Exception):
    pass
