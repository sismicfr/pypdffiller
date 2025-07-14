import shutil
from pathlib import Path

import pytest

import pdffiller
from pdffiller.typing import Generator


@pytest.fixture(scope="session")
def test_dir(pytestconfig) -> Path:
    """Retrieve path to tests directory from test environment"""
    return pytestconfig.rootdir / "tests"


@pytest.fixture(scope="session")
def test_data_dir(pytestconfig) -> Path:
    """Retrieve path to tests data directory from test environment"""
    return pytestconfig.rootdir / "tests" / "data"


@pytest.fixture(name="tmp_output_dir")
def fixture_tmp_output_dir(tmp_path) -> Generator[Path, None, None]:
    """Generate temporary history file"""
    local_output_dir = tmp_path / "_output"
    local_output_dir.mkdir(parents=True)
    yield local_output_dir
    shutil.rmtree(local_output_dir)
