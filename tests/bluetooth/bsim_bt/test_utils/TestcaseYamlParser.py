from strictyaml import load as strictyaml_load
from strictyaml import Map, MapPattern, Optional, Seq, Str, YAMLError
import pytest

class TestcaseYamlParser:
    bsim_config_schema = Map(
        {
            "devices": Seq(Map(
                {
                    "id": Str(),
                    Optional("extra_run_args"): Seq(Str()),
                }
            )),
            "medium": Map(
                {
                    "name": Str(),
                    "sim_length": Str(),
                    Optional("extra_run_args"): Seq(Str()),
                }
            ),
        }
    )

    testscenario_schema = Map(
        {
            Optional("bsim_config"): bsim_config_schema,
            Optional("extra_args"): Seq(Str()),
            Optional("platform_allow"): Str(),
            Optional("tags"): Str(),
        }
    )

    tests_schema = MapPattern(
        Str(),  # testscenario name
        testscenario_schema,
        minimum_keys=1,  # tests require minimum one testscenario
    )

    testcase_yaml_schema = Map(
        {
            # TODO: add common_schema
            "tests": tests_schema,
        }
    )

    def __init__(self):
        pass

    def load(self, testcase_yaml_fspath):
        with open(testcase_yaml_fspath, "r") as file_handler:
            try:
                yaml_data = strictyaml_load(
                    file_handler.read(),
                    self.testcase_yaml_schema
                )
            except YAMLError as err:
                if hasattr(err, "context"):
                    err.context = f"while parsing a file \n" \
                                  f"{testcase_yaml_fspath}\n" + err.context
                raise err
            yaml_data = yaml_data.data
        return yaml_data
