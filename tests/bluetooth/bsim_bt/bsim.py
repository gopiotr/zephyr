
class BsimDevice():
    def __init__(self, exe_path, testid=None, extra_args=None):
        self.exe_path = exe_path
        self.testid = testid
        self.extra_args = extra_args
        self.output = ""


class BsimPhy():
    def __init__(self, type, extra_args=None):
        self.type = type
        self.extra_args = extra_args
        self.output = ""


class BsimRunner():
    def __init__(self, devices, phy):
        self.devices = devices
        self.phy = phy

    def run(self):
        pass
