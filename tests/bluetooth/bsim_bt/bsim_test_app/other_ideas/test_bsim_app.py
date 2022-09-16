import pytest
import sys

sys.path.append('..')
from bsim import BsimDevice, BsimPhy, BsimRunner


@pytest.fixture(scope="module")
def build():
    built_exe_path = f""
    print("Building finished")
    return built_exe_path


TEST_CONFIGS = [
    {
        "name": "basic_conn_encrypted_split_privacy",
        "configs": {
            "exe_name": "bs_nrf52_bsim_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_privacy_conf",
            "peripheral_id": "peripheral",
            "peripheral_extra_args": "-RealEncryption=1 -rs=23",
            "central_id": "central_encrypted",
            "central_extra_args": "-RealEncryption=1 -rs=6",
            "phy_extra_args": "sim_length=20e6",
        }
    },
    {
        "name": "basic_conn_encrypted_split",
        "configs": {
            "exe_name": "bs_nrf52_bsim_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_conf",
            "peripheral_id": "peripheral",
            "peripheral_extra_args": "-RealEncryption=1 -rs=23",
            "central_id": "central_encrypted",
            "central_extra_args": "-RealEncryption=1 -rs=6",
            "phy_extra_args": "sim_length=20e6",
        }
    },
    {
        "name": "basic_conn_split_low_lat",
        "configs": {
            "exe_name": "bs_nrf52_bsim_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_low_lat_conf",
            "peripheral_id": "peripheral",
            "peripheral_extra_args": "-RealEncryption=0 -rs=23",
            "central_id": "central",
            "central_extra_args": "-RealEncryption=0 -rs=6",
            "phy_extra_args": "sim_length=20e6",
        }
    },
    {
        "name": "basic_conn_split",
        "configs": {
            "exe_name": "bs_nrf52_bsim_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_conf",
            # "dut": [
            #     {
            #         "id": "peripheral",
            #         "extra_args": "-RealEncryption=0 -rs=23",
            #     },
            #     {
            #         "id": "central",
            #         "extra_args": "-RealEncryption=0 -rs=26",
            #     }
            # ]
            "peripheral_id": "peripheral",
            "peripheral_extra_args": "-RealEncryption=0 -rs=23",
            "central_id": "central",
            "central_extra_args": "-RealEncryption=0 -rs=6",
            "phy_extra_args": "sim_length=20e6",
        }
    },
]

ARGNAMES = [argname for argname in TEST_CONFIGS[0]["configs"].keys()]
ARGVALUE = tuple([list(test_config["configs"].values()) for test_config in TEST_CONFIGS])
IDS = [test_config["name"] for test_config in TEST_CONFIGS]


# TESTDATA = [
#     ("bs_nrf52_bsim_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_privacy_conf", "peripheral", "-RealEncryption=1 -rs=23", "central_encrypted", "-RealEncryption=1 -rs=6", "-sim_length=20e6"),
#     ("bs_nrf52_bsim_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_conf", "peripheral", "-RealEncryption=1 -rs=23", "central_encrypted", "-RealEncryption=1 -rs=6", "-sim_length=20e6"),
#     ("bs_nrf52_bsim_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_low_lat_conf", "peripheral", "-RealEncryption=0 -rs=23", "central", "-RealEncryption=0 -rs=6", "-sim_length=20e6"),
#     ("bs_nrf52_bsim_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_conf", "peripheral", "-RealEncryption=0 -rs=23", "central", "-RealEncryption=0 -rs=6", "-sim_length=20e6"),
# ]


# IDS = [
#     "basic_conn_encrypted_split_privacy",
#     "basic_conn_encrypted_split",
#     "basic_conn_split_low_lat",
#     "basic_conn_split",
# ]


# @pytest.mark.parametrize("exe_name, peripheral_id, peripheral_extra_args, central_id, central_extra_args, phy_extra_args", TESTDATA, ids=IDS)
@pytest.mark.parametrize(ARGNAMES, ARGVALUE, ids=IDS)
def test_app(build, exe_name, peripheral_id, peripheral_extra_args, central_id, central_extra_args, phy_extra_args, parser):

    devices = [
        BsimDevice(exe_path=exe_name, testid=peripheral_id, extra_args=peripheral_extra_args),
        BsimDevice(exe_path=exe_name, testid=central_id, extra_args=central_extra_args),
    ]
    phy = BsimPhy(type="24G", extra_args=phy_extra_args)

    bsim_runner = BsimRunner(devices=devices, phy=phy)
    bsim_runner.run()

    for device in bsim_runner.devices:
        parser.parse(device.output)
