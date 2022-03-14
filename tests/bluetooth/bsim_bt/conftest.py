
import pytest
from test_utils.BabbleSimBuild import BabbleSimBuild
from test_utils.BabbleSimRun import BabbleSimRun

def pytest_collect_file(parent, path):
    if path.basename.startswith("bs_testcase") and (path.ext == ".yaml" or path.ext == ".yml"):
        return YamlFile.from_parent(parent, fspath=path)


class YamlFile(pytest.File):
    def collect(self):
        import yaml

        with self.fspath.open() as file_handler:
            raw = yaml.safe_load(file_handler)

        # pytest.set_trace()
        test_path = self.fspath.dirpath()
        for testscenario_name, specification in raw["tests"].items():
            yield YamlItem.from_parent(self, test_path=test_path, testscenario_name=testscenario_name, specification=specification)


class YamlItem(pytest.Item):
    def __init__(self, parent, test_path, testscenario_name, specification):
        super().__init__(testscenario_name, parent)
        self.test_path = test_path
        self.specification = specification

        # TODO: change simulation_id to test name (which has to be unique)
        if "simulation_id" in specification:
            self.simulation_id = specification["simulation_id"]
        else:
            print("simulation_id not defined in bs_testcase.yaml!")
            self.simulation_id = "simulation_id"

        # TODO: Refactor for better handling of testid values
        if "testid_0" in specification and "testid_1" in specification:
            self.testid_0 = specification["testid_0"]
            self.testid_1 = specification["testid_1"]
        else:
            print("testid not defined in bs_testcase.yaml!")
            self.testid_0 = "testid_0"
            self.testid_1 = "testid_1"

    def runtest(self):
        bs_builder = BabbleSimBuild(self.test_path)
        exe_path = bs_builder.build()
        bs_runner = BabbleSimRun(self.simulation_id)
        bs_runner.run(exe_path_0=exe_path, testid_0=self.testid_0, exe_path_1=exe_path, testid_1=self.testid_1)
        if False:
            raise YamlException(self)

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        if isinstance(excinfo.value, YamlException):
            return "Test fails"


class YamlException(Exception):
    pass
