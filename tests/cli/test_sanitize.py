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


@pytest.mark.parametrize("argv", [])
def test_incomplete(argv):
    """test command without required arguments"""

    # Test through direct command-line
    with mock.patch("sys.argv", ["pdffiller", "sanitize"] + argv):
        assert cli.main() == ERROR_UNEXPECTED

    # Test with direct call to main function
    assert cli.main(["sanitize"] + argv) == ERROR_UNEXPECTED


def test_complete(test_data_dir, output_pdf_path, capsys):
    """test sanitize command with text output"""

    argv = [
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    # Test through direct command-line
    with mock.patch(
        "sys.argv",
        ["pdffiller", "sanitize"] + argv,
    ):
        assert cli.main() == SUCCESS
        assert output_pdf_path.exists()
        output_pdf_path.unlink()

    # Test with direct call to main function
    assert cli.main(["sanitize"] + argv) == SUCCESS
    assert output_pdf_path.exists()


def test_complete_json_output(test_data_dir, output_pdf_path, capsys):
    """test sanitize command with JSON output"""

    argv = [
        "-fjson",
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    with mock.patch(
        "sys.argv",
        ["pdffiller", "sanitize"] + argv,
    ):
        assert cli.main() == SUCCESS
        out, err = capsys.readouterr()
        # Output should be valid JSON (or empty if no fields to sanitize)
        if out.strip():
            sanitized = json.loads(out)
            assert isinstance(sanitized, list)
            for field in sanitized:
                assert "FieldName" in field
                assert "FieldType" in field
                assert "MaxLen" in field


def test_complete_with_deep(test_data_dir, output_pdf_path):
    """test sanitize command with --deep option"""

    argv = [
        "--deep",
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    # Test through direct command-line
    with mock.patch(
        "sys.argv",
        ["pdffiller", "sanitize"] + argv,
    ):
        assert cli.main() == SUCCESS
        assert output_pdf_path.exists()
        output_pdf_path.unlink()

    # Test with direct call to main function
    assert cli.main(["sanitize"] + argv) == SUCCESS
    assert output_pdf_path.exists()


def test_complete_with_invalid_file(test_data_dir, output_pdf_path):
    """test sanitize command with invalid PDF"""

    argv = [
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "empty.pdf"),
    ]

    # PdfFillerException is caught and logged, command returns SUCCESS
    # Test through direct command-line
    with mock.patch(
        "sys.argv",
        ["pdffiller", "sanitize"] + argv,
    ):
        assert cli.main() == SUCCESS

    # Test with direct call to main function
    assert cli.main(["sanitize"] + argv) == SUCCESS
