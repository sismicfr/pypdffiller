import json
from unittest import mock

import pytest

from pdffiller.cli import cli
from pdffiller.cli.exit_codes import (
    ERROR_COMMAND_NAME,
    ERROR_ENCOUNTERED,
    ERROR_UNEXPECTED,
    SUCCESS,
)
from pdffiller.pdf import Pdf


def test_incomplete_no_action():
    """test empty command-line"""

    with mock.patch("sys.argv", []):
        assert cli.main() == ERROR_COMMAND_NAME


@pytest.mark.parametrize("argv", [])
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


@pytest.mark.parametrize(
    "input_data",
    [
        '[{"name": "Lastname", "value": "Doe"}, {"name": "Men", "value": "On"}]',
        '[{"FieldName": "Lastname", "FieldValue": "Doe"}, {"FieldName": "Men"}]',
        '[{"name": "Lastname", "value": 42}, {"name": "Men", "value": true}]',
        '[{"name": "Lastname", "value": null}]',
        "[]",
        '{"Lastname": "Doe", "Men": true}',
    ],
)
def test_complete_with_list_input_data(test_data_dir, output_pdf_path, input_data):
    """test the supported input data layouts given on the command-line"""

    argv = [
        "-i",
        input_data,
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    assert cli.main(["fill_form"] + argv) == SUCCESS
    assert output_pdf_path.exists()


@pytest.mark.parametrize(
    "input_data",
    [
        '["Lastname"]',
        "42",
        '[{"Readonly": true}]',
        '{"Lastname": ["Doe"]}',
    ],
)
def test_complete_with_invalid_input_data(test_data_dir, output_pdf_path, input_data):
    """test that an unsupported input data layout is reported without traceback"""

    argv = [
        "-i",
        input_data,
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    assert cli.main(["fill_form"] + argv) == ERROR_ENCOUNTERED
    assert not output_pdf_path.exists()


@pytest.mark.parametrize("extension", [".json", ".yaml", ".yml"])
@pytest.mark.parametrize("content", ["[]", "{}"])
def test_complete_with_empty_data_file(
    test_data_dir, output_pdf_path, tmp_path, capsys, extension, content
):
    """test a data file holding an empty array/mapping, thus no field to fill in"""

    data_path = tmp_path / f"empty{extension}"
    data_path.write_text(content, encoding="utf-8")

    argv = [
        "-d",
        str(data_path),
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    assert cli.main(["fill_form"] + argv) == SUCCESS
    assert "no field value to fill in" in capsys.readouterr().err

    # The input pdf is copied as is, keeping all its form fields untouched
    assert output_pdf_path.exists()
    assert Pdf(str(output_pdf_path)).schema == Pdf(str(test_data_dir / "input.pdf")).schema


@pytest.mark.parametrize("extension", [".yaml", ".yml"])
def test_complete_with_void_yaml_data_file(
    test_data_dir, output_pdf_path, tmp_path, capsys, extension
):
    """test a void yaml data file, which yaml loads as no data at all"""

    data_path = tmp_path / f"void{extension}"
    data_path.write_text("", encoding="utf-8")

    argv = [
        "-d",
        str(data_path),
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    assert cli.main(["fill_form"] + argv) == SUCCESS
    assert "no field value to fill in" in capsys.readouterr().err
    assert output_pdf_path.exists()


def test_complete_with_void_json_data_file(test_data_dir, output_pdf_path, tmp_path, capsys):
    """test a void json data file, which is not a valid json document"""

    data_path = tmp_path / "void.json"
    data_path.write_text("", encoding="utf-8")

    argv = [
        "-d",
        str(data_path),
        "-o",
        str(output_pdf_path),
        str(test_data_dir / "input.pdf"),
    ]

    assert cli.main(["fill_form"] + argv) == ERROR_ENCOUNTERED
    assert f"Failed to load {data_path} input data file" in capsys.readouterr().err
    assert not output_pdf_path.exists()
