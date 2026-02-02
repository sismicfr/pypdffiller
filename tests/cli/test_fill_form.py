import json
from unittest import mock

import pytest

from pdffiller.cli import cli
from pdffiller.cli.exit_codes import (
    ERROR_COMMAND_NAME,
    ERROR_UNEXPECTED,
    SUCCESS,
)

def test_incomplete_no_action():
    """test empty command-line"""

    with mock.patch("sys.argv", []):
        assert cli.main() == ERROR_COMMAND_NAME


@pytest.mark.parametrize(
    "argv",
    []
)
def test_incomplete(argv):
    """test empty command-line"""

    # Test through direct command-line
    with mock.patch("sys.argv", ["pdffiller", "fill_form"] + argv):
        assert cli.main() == ERROR_UNEXPECTED

    # Test with direct call to main function
    assert cli.main(["fill_form"] + argv) == ERROR_UNEXPECTED


def test_complete_with_files_only(test_data_dir, input_json_fields, output_pdf_path):
    """test complete command-line"""

    argv = [
        "-d",
        str(input_json_fields),
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    # Test through direct command-line
    with mock.patch(
        "sys.argv",
        ["pdffiller", "fill_form"] + argv,
    ):
        assert cli.main() == SUCCESS
        assert output_pdf_path.exists()
        output_pdf_path.unlink()

    # Test with direct call to main function
    assert cli.main(["fill_form"] + argv) == SUCCESS
    assert output_pdf_path.exists()


def test_complete_with_invalid_file(test_data_dir, input_json_fields, output_pdf_path):
    """test complete command-line"""

    argv = [
        "-d",
        input_json_fields,
        "-o",
        output_pdf_path,
        str(test_data_dir / "empty.pdf"),
    ]

    # Test through direct command-line
    with mock.patch(
        "sys.argv",
        ["pdffiller", "fill_form"] + argv,
    ):
        assert cli.main() == ERROR_UNEXPECTED

    # Test with direct call to main function
    assert cli.main(["fill_form"] + argv) == ERROR_UNEXPECTED

def test_complete_with_file_and_string(test_data_dir, input_json_fields, output_pdf_path):
    """test complete command-line"""

    json_fields = input_json_fields.read_text()
    argv = [
        "-i",
        json_fields,
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    # Test through direct command-line
    with mock.patch(
        "sys.argv",
        ["pdffiller", "fill_form"] + argv,
    ):
        assert cli.main() == SUCCESS
        assert output_pdf_path.exists()
        output_pdf_path.unlink()

    # Test with direct call to main function
    assert cli.main(["fill_form"] + argv) == SUCCESS
    assert output_pdf_path.exists()

