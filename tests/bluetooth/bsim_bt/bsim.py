import logging
import time
import pytest


logger = logging.getLogger(__name__)


def bsim_test_run(duts):
    run_duts(duts)
    wait_for_duts(duts)
    stop_duts(duts)
    log_output_duts(duts)
    check_duts_return_code(duts)


def run_duts(duts):
    for dut in duts.values():
        dut.flash_and_run()


def wait_for_duts(duts):
    should_wait = True
    while should_wait:
        time.sleep(0.5)
        return_codes = get_return_codes(duts)
        should_wait = None in return_codes


def get_return_codes(duts):
    return_codes = []
    for dut in duts.values():
        return_codes.append(dut._process.returncode)
    return return_codes


def stop_duts(duts):
    for dut in duts.values():
        dut.stop()


def check_duts_return_code(duts):
    for dut_name, dut in duts.items():
        return_code = dut._process.returncode
        if return_code is None or return_code != 0:
            msg = f'Return code of "{dut_name}" DUT is {return_code}'
            logger.error(msg)
            pytest.fail(msg)


def log_output_duts(duts):
    for dut_name, dut in duts.items():
        logger.info(dut_name)
        for line in dut.iter_stdout:
            logger.info(line)
