import time
import re
import pytest

@pytest.mark.build_specification
def test_shell(specification, dut):
    time.sleep(5)  # wait for application initialization on DUT

    dut.connection.write(b'help\n')

    pattern = re.compile('.*Please press the <Tab> button to see all available commands.*')
    matched = False
    timeout = 5  # [sec]
    time_end = time.time() + timeout
    for line in dut.iter_stdout:
        if pattern.match(line):
            matched = True
            break
        if time.time() > time_end:
            break

    assert matched
