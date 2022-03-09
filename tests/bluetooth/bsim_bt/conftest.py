
import pytest

def pytest_collect_file(parent, path):
    if path.ext == ".yaml" or path.ext == ".yml" and path.basename.startswith("test"):
        return YamlFile.from_parent(parent, fspath=path)


class YamlFile(pytest.File):
    def collect(self):
        import yaml

        with self.fspath.open() as file_handler:
            raw = yaml.safe_load(file_handler)

        for testscenario_name, specification in raw["tests"].items():
            yield YamlItem.from_parent(self, testscenario_name=testscenario_name, specification=specification)


class YamlItem(pytest.Item):
    def __init__(self, parent, testscenario_name, specification):
        super().__init__(testscenario_name, parent)
        self.specification = specification

    def runtest(self):
        # TODO: Build, run, verify
        if False:
            raise YamlException(self, name, value)

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        if isinstance(excinfo.value, YamlException):
            return "Test fails"


class YamlException(Exception):
    pass
