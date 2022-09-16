import pytest
import sys

sys.path.append('..')
from bsim import BsimDevice, BsimPhy, BsimRunner


TESTDATA = [
    ("gatt_client_db_hash_read_eatt", "gatt_server_eatt", "-sim_length=60e6"),
    ("gatt_client_db_hash_read_no_eatt", "gatt_server_no_eatt", "-sim_length=60e6"),
    ("gatt_client_out_of_sync_eatt", "gatt_server_eatt", "-sim_length=60e6"),
    ("gatt_client_out_of_sync_no_eatt", "gatt_server_no_eatt", "-sim_length=60e6"),
    ("gatt_client_retry_reads_eatt", "gatt_server_eatt", "-sim_length=60e6"),
    ("gatt_client_retry_reads_no_eatt", "gatt_server_no_eatt", "-sim_length=60e6"),
]


IDS = [
    "gatt_caching_db_hash_read_eatt",
    "gatt_caching_db_hash_read_no_eatt",
    "gatt_caching_out_of_sync_eatt",
    "gatt_caching_out_of_sync_no_eatt",
    "gatt_caching_retry_reads_eatt",
    "gatt_caching_retry_reads_no_eatt",
]


@pytest.mark.parametrize("client_id, server_id, phy_extra_args", TESTDATA, ids=IDS)
def test_gatt_caching(build, client_id, server_id, phy_extra_args, parser):

    devices = [
        BsimDevice(exe_path=build, testid=client_id),
        BsimDevice(exe_path=build, testid=server_id),
    ]
    phy = BsimPhy(type="24G", extra_args=phy_extra_args)

    bsim_runner = BsimRunner(devices=devices, phy=phy)
    bsim_runner.run()

    for device in bsim_runner.devices:
        parser.parse(device.output)
