import pytest
from pathlib import Path
import time
import os
from posix_ipc import Semaphore, O_CREAT
from filelock import FileLock
import tempfile
from twister2.builder.builder_abstract import BuilderAbstract
from twister2.builder.build_manager import BuildManager, BuildConfig


@pytest.mark.build_specification
def test_hello_world_1(request):
    run_build(request)
    verify(request)


@pytest.mark.build_specification
def test_hello_world_2(request):
    run_build(request)
    verify(request)


@pytest.mark.build_specification
def test_hello_world_3(request):
    run_build(request)
    verify(request)


@pytest.mark.build_specification
def test_hello_world_4(request):
    run_build(request)
    verify(request)


class DummyBuilder(BuilderAbstract):
    def __init__(self, test_name) -> None:
        super().__init__()
        self.test_name = test_name

    def build(self, build_config: BuildConfig) -> None:
        time.sleep(1)
        os.makedirs(build_config.build_dir, exist_ok=True)
        file_path = build_config.build_dir / self.test_name
        with open(file_path, "w") as file:
            pass


def run_build(request):
    test_name = get_plain_test_name(request.node.name)
    spec = request.session.specifications[request.node.nodeid]
    twister_config = request.config.twister_config
    spec.output_dir = Path(twister_config.output_dir).resolve()

    builder = DummyBuilder(test_name)
    build_config = BuildConfig(
        zephyr_base=twister_config.zephyr_base,
        source_dir=spec.source_dir,
        platform=spec.platform,
        build_dir=spec.build_dir,
        scenario=spec.scenario,
        extra_args=spec.extra_args
    )
    build_manager = BuildManager(request.config.option.output_dir)

    # synchronize(test_name)
        
    build_manager.build(builder, build_config)


def verify(request):
    spec = request.session.specifications[request.node.nodeid]
    number_of_files = len(list(spec.build_dir.iterdir()))
    assert number_of_files == 1


def get_plain_test_name(nodeid):
    name = nodeid
    name = name.replace("[", "_")
    name = name.replace("]", "")
    name = name.replace(".", "_")
    name = name.replace(":", "_")
    name = name.replace("-", "_")
    return name


def synchronize(test_name):
    # mq = MessageQueue("/test_hello_world", flags=O_CREAT)

    _TMP_DIR: str = tempfile.gettempdir()
    BUILD_LOCK_FILE_PATH: str = os.path.join(_TMP_DIR, 'hello_world_test.lock')

    lock = FileLock(BUILD_LOCK_FILE_PATH)

    if test_name != 'test_hello_world_1_native_posix_sample_basic_helloworld':
        time.sleep(1)

    with lock:
        print(test_name)
        if test_name == 'test_hello_world_1_native_posix_sample_basic_helloworld':
            time.sleep(2)

    # with Semaphore("/test_hello_world_2", flags=O_CREAT, initial_value=1):
    #     if test_name == 'test_hello_world_2_native_posix_sample_basic_helloworld':
    #         time.sleep(1)