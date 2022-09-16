import pytest
import sys

sys.path.append('..')
from bsim import BsimDevice, BsimPhy, BsimRunner


@pytest.mark.build_specification('bluetooth.bsim.app_split_build')
def test_app_split(request, specification, builder, devices_config):
    pass


@pytest.mark.build_specification('bluetooth.bsim.app_split_low_lat_build')
def test_app_split_low_lat(request, specification, builder, devices_config):
    pass


@pytest.mark.build_specification('bluetooth.bsim.app_split_privacy_encrypted_build')
def test_app_split_privacy_encrypted(request, specification, builder, devices_config):
    pass

