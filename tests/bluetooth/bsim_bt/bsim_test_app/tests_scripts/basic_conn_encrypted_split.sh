#!/usr/bin/env bash
# Copyright 2018 Oticon A/S
# SPDX-License-Identifier: Apache-2.0

# Basic connection test: a central connects to a peripheral and expects a
# notification
simulation_id="basic_conn_encr_split"
verbosity_level=2
process_ids=""; exit_code=0

function Execute(){
  if [ ! -f $1 ]; then
    echo -e "  \e[91m`pwd`/`basename $1` cannot be found (did you forget to\
 compile it?)\e[39m"
    exit 1
  fi

  test_id=`echo "$6" | cut -c 9-`
  log_dir_path="/home/redbeard/zephyrproject/zephyr/bsim_bt_out/parallel_tests_output/${simulation_id}"
  mkdir -p ${log_dir_path}
  out_file_path="${log_dir_path}/${test_id}_out.log"
  err_file_path="${log_dir_path}/${test_id}_err.log"

  timeout 5 $@ 1>$out_file_path 2> $err_file_path & process_ids="$process_ids $!"
}

: "${BSIM_OUT_PATH:?BSIM_OUT_PATH must be defined}"

#Give a default value to BOARD if it does not have one yet:
BOARD="${BOARD:-nrf52_bsim}"

cd ${BSIM_OUT_PATH}/bin

Execute ./bs_${BOARD}_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_conf \
  -v=${verbosity_level} -s=${simulation_id} -d=0 -RealEncryption=1 \
  -testid=peripheral -rs=23

Execute ./bs_${BOARD}_tests_bluetooth_bsim_bt_bsim_test_app_prj_split_conf \
  -v=${verbosity_level} -s=${simulation_id} -d=1 -RealEncryption=1 \
  -testid=central_encrypted -rs=6

Execute ./bs_2G4_phy_v1 -v=${verbosity_level} -s=${simulation_id} \
  -D=2 -sim_length=20e6 $@

for process_id in $process_ids; do
  wait $process_id || let "exit_code=$?"
done
exit $exit_code #the last exit code != 0
