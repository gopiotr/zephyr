import pytest
import sys

sys.path.append('..')
from bsim import bsim_test_run


@pytest.mark.build_specification('bluetooth.bsim.app_split_build')
def test_app_split(specification, builder, duts):
    bsim_test_run(duts)


@pytest.mark.build_specification('bluetooth.bsim.app_split_low_lat_build')
def test_app_split_low_lat(specification, builder, duts):
    bsim_test_run(duts)


@pytest.mark.build_specification('bluetooth.bsim.app_split_privacy_encrypted_build')
def test_app_split_privacy_encrypted(specification, builder, duts):
    bsim_test_run(duts)

