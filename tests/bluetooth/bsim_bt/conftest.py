import pytest
from test_utils.TestcaseYamlParser import TestcaseYamlParser
from test_utils.BabbleSimBuild import BabbleSimBuild
from test_utils.BabbleSimRun import BabbleSimRun


def pytest_collect_file(parent, path):
    if path.basename.startswith("bs_testcase") and (path.ext == ".yaml" or path.ext == ".yml"):
        return YamlFile.from_parent(parent, fspath=path)


class YamlFile(pytest.File):
    def collect(self):
        test_path = self.fspath.dirpath()

        parser = TestcaseYamlParser()
        yaml_data = parser.load(self.fspath)
        testscenarios = yaml_data.get("tests", {})
        for testscenario_name, testscenario_config in testscenarios.items():
            if "bsim_config" not in testscenario_config:
                continue
            yield YamlItem.from_parent(
                self,
                test_path=test_path,
                testscenario_name=testscenario_name,
                testscenario_config=testscenario_config
            )


class YamlItem(pytest.Item):
    def __init__(self, parent, test_path, testscenario_name,
                 testscenario_config):
        super().__init__(testscenario_name, parent)
        self.test_path = test_path
        self.extra_build_args = testscenario_config.get("extra_args", [])

        self.sim_id = testscenario_name.replace(".", "_")

        bsim_config = testscenario_config["bsim_config"]
        self.devices = bsim_config.get("devices", [])
        self.medium = bsim_config.get("medium", {})

    def runtest(self):
        bs_builder = BabbleSimBuild(
            self.test_path,
            extra_build_args=self.extra_build_args
        )
        exe_path = bs_builder.build()

        bs_runner = BabbleSimRun(
            self.sim_id,
            exe_path,
            self.devices,
            self.medium
        )
        bs_runner.run()
        if False:
            raise YamlException(self)

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        if isinstance(excinfo.value, YamlException):
            return "Test fails"


class YamlException(Exception):
    pass
