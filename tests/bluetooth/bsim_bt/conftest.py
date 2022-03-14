
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

    def runtest(self):
        bs_builder = BabbleSimBuild(self.test_path)
        exe_path = bs_builder.build()
        bs_runner = BabbleSimRun(exe_path)
        bs_runner.run()
        if False:
            raise YamlException(self)

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        if isinstance(excinfo.value, YamlException):
            return "Test fails"


class YamlException(Exception):
    pass
