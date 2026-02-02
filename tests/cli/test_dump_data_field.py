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
    with mock.patch("sys.argv", ["pdffiller", "dump_data_fields"] + argv):
        assert cli.main() == ERROR_UNEXPECTED

    # Test with direct call to main function
    assert cli.main(["dump_data_fields"] + argv) == ERROR_UNEXPECTED


def test_complete(test_data_dir, capsys):
    """test complete command-line"""

    argv = [
        str(test_data_dir / "input.pdf"),
    ]

    json_fields = """[
    {
        "FieldType": "text",
        "FieldName": "Lastname"
    },
    {
        "FieldType": "text",
        "FieldName": "Firstname"
    },
    {
        "FieldType": "checkbox",
        "FieldOptions": [
            "Off",
            "Oui"
        ],
        "FieldName": "Men"
    },
    {
        "FieldType": "checkbox",
        "FieldOptions": [
            "Off",
            "Oui"
        ],
        "FieldName": "Women"
    },
    {
        "FieldType": "radio",
        "FieldOptions": [
            "Off",
            "Single",
            "Married",
            "Divorced"
        ],
        "FieldName": "MaritalStatus",
        "FieldValue": "Off"
    }
]"""
    # Test through direct command-line
    with mock.patch(
        "sys.argv",
        ["pdffiller", "dump_data_fields", "-fjson"] + argv,
    ):
        assert cli.main() == SUCCESS
        out, err = capsys.readouterr()
        assert "loading file in memory" == err.strip()
        assert json.loads(json_fields) == json.loads(out)

    # Test with direct call to main function
    assert cli.main(["dump_data_fields"] + argv) == SUCCESS


def test_complete_with_invalid_file(test_data_dir):
    """test complete command-line"""

    argv = [
        str(test_data_dir / "empty.pdf"),
    ]

    # Test through direct command-line
    with mock.patch(
        "sys.argv",
        ["pdffiller", "dump_data_fields"] + argv,
    ):
        assert cli.main() == ERROR_UNEXPECTED

    # Test with direct call to main function
    assert cli.main(["dump_data_fields"] + argv) == ERROR_UNEXPECTED

