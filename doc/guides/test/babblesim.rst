.. _babblesim:

BabbleSim tests support
#######################

Tests dedicated for BabbleSim simulator require special build and run workflow
and at this moment they cannot be run by Twister test runner. To solve this
problem special Pytest plugin was designed.

Pytest plugin
*************

In usual case Pytest test runner is used most often for Python unit tests.
However, thanks to the extensive system of hooks and plugins Pytest make it
possible to define how tests gathering should looks like and what should be
performed during test run. It enables to design own plugin dedicated for
BabbleSim tests.

Using Pytest test runner allow to use ready-made functionalities as:

- scanning directories for tests' definitions
- filtering tests by name (including/excluding tests)
- tests execution and storing tests' results
- generating several types of test report (``junit`` (``xml``), ``json``,
  ``html``)
- splitting tests into sub-groups (by ``split-tests`` plugin)
- running tests in parallel (by ``xdist`` plugin)

How to run tests?
*****************

To run BabbleSim tests defined to run by Pytest, following environmental
variables have to be exported (of course below paths may vary depending on
user's Zephyr and BabbleSim installation place):

::

    export ZEPHYR_BASE="${HOME}/zephyrproject/zephyr"
    export BSIM_OUT_PATH="${HOME}/bsim/"
    export BSIM_COMPONENTS_PATH="${HOME}/bsim/components/"

Next below command should be called:

::

    pytest tests/bluetooth/bsim_bt

Exemplary output could looks like:

::

    ========================= test session starts ==========================
    platform linux -- Python 3.8.10, pytest-6.2.4, py-1.10.0, pluggy-0.13.1
    rootdir: /home/redbeard/zephyrproject/zephyr
    plugins: typeguard-2.13.3, forked-1.4.0, xdist-2.5.0
    collected 8 items

    tests/bluetooth/bsim_bt/bsim_test_advx/bs_testcase.yaml .        [ 12%]
    tests/bluetooth/bsim_bt/bsim_test_app/bs_testcase.yaml ....      [ 62%]
    tests/bluetooth/bsim_bt/bsim_test_eatt/bs_testcase.yaml ..       [ 87%]
    tests/bluetooth/bsim_bt/bsim_test_gatt/bs_testcase.yaml .        [100%]

    ===================== 8 passed in 67.68s (0:01:07) =====================

For more verbose output special arguments could be added to basic command:

::

    pytest tests/bluetooth/bsim_bt -vv log_cli=true

How it works?
*************

BabbleSim tests are defined in ``bs_testcase.yaml`` files (similar to "classic"
Twister approach with defining tests in ``testcase.yaml`` files). At the
beginning Pytest scan directories and try to find ``bs_testcase.yaml`` and
tests defined inside it. Exemplary ``bs_testcase.yaml`` for
``tests/bluetooth/bsim_bt/bsim_test_gatt`` test may look like below:

.. code-block:: yaml

    tests:
      bluetooth.bsim.gatt:
        platform_allow:
          - nrf52_bsim
        tags:
          - bluetooth
        extra_args:
          - '-DCMAKE_C_FLAGS="-Werror"'
          - "-DCONFIG_COVERAGE=y"
          - "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
        bsim_config:
          devices:
            -
              id: gatt_client
            -
              id: gatt_server
          medium:
            name: bs_2G4_phy_v1
            sim_length: 60e6

This YAML file define necessary information to build and run BabbleSim's tests.
Next after collecting all tests, Pytest filter tests if some filter rules were
passed in CLI.

Each test consists of two phase:

1. Building process
    - get CMake extra arguments from ``bs_testcase.yaml`` file and prepare CMake
      command (add source code directory, output build directory, target
      platform (``nrf52_bsim``), conf file (if was not passed explicitly in
      ``extra_args`` option))
    - run CMake
    - run Ninja generator
2. Run simulation
    - parse ``bsim_config`` from ``bs_testcase.yaml`` file and prepare suitable
      commands to run each simulated devices and wireless medium
    - run simulation
    - if some error/failure occurs during run simulation then mark test as
      ``FAILED`` - otherwise as ``PASSED``

Final report is generated at the end if adequate argument was passed through CLI
(for example ``--junitxml=./bs_report.xml``).

Minimal test configuration
**************************

Additional features
*******************

Parallelization
***************

Plugin debugging
****************
