import pytest
import sys

sys.path.append('..')
from bsim import bsim_test_run


@pytest.mark.build_specification('bluetooth.bsim.app_split_build')
def test_app_split(builder, duts):
    bsim_test_run(duts)


@pytest.mark.build_specification('bluetooth.bsim.app_split_low_lat_build')
def test_app_split_low_lat(builder, duts):
    bsim_test_run(duts)


@pytest.mark.build_specification('bluetooth.bsim.app_split_privacy_encrypted_build')
def test_app_split_privacy_encrypted(builder, duts):
    bsim_test_run(duts)

