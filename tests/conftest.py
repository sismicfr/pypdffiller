import shutil
from pathlib import Path

import pytest

import time
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


@pytest.fixture(name="input_json_fields")
def fixture_dynamic_config_file(tmp_path) -> Generator[Path, None, None]:
    """Generate temporary input json file"""
    config_path = tmp_path / "input.json"

    json_content = """[
    {
        "name": "Lastname",
        "value": "Doe"
    },
    {
        "name": "Firstname",
        "value": "John"
    },
    {
        "name": "Men",
        "value": "On"
    },
    {
        "name": "Women",
        "value": ""
    },
    {
        "name": "MaritalStatus",
        "value": "Single"
    }
]
    """
    config_path.write_text(json_content)
    yield config_path
    config_path.unlink()

@pytest.fixture(name="output_pdf_path")
def fixture_output_pdf_path(tmp_path) -> Generator[Path, None, None]:
    """Generate temporary output pdf file"""
    output_path = tmp_path / f"{time.time()}.pdf"
    yield output_path
    if output_path.exists():
        output_path.unlink()
