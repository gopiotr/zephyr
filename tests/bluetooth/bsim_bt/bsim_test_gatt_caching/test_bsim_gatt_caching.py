import sys
import pytest

sys.path.append('..')
from bsim import bsim_test_run


def test_gatt_caching(specification, builder, duts):
    bsim_test_run(duts)