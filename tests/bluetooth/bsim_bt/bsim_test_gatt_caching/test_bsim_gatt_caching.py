import sys
import pytest

sys.path.append('..')
from bsim import bsim_test_run


@pytest.mark.build_specification
def test_gatt_caching(builder, duts):
    bsim_test_run(duts)