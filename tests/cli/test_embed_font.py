import json

import pymupdf
import pytest

from pdffiller.cli import cli
from pdffiller.cli.exit_codes import ERROR_ENCOUNTERED, ERROR_UNEXPECTED, SUCCESS


@pytest.fixture(name="font_path")
def fixture_font_path(test_data_dir):
    return str(test_data_dir / "fonts" / "DejaVuSansMono.ttf")


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["-o", "out.pdf"],
        ["--font", "font.ttf", "input.pdf"],
        ["-o", "out.pdf", "input.pdf"],
    ],
)
def test_incomplete(argv):
    """test command without required arguments"""
    assert cli.main(["embed_font"] + argv) == ERROR_UNEXPECTED


def test_complete_json_output(test_data_dir, font_path, output_pdf_path, capsys):
    """every text field names the embedded font, which is in the form resources"""
    argv = ["-fjson", "--font", font_path, "-o", str(output_pdf_path)]
    assert cli.main(["embed_font"] + argv + [str(test_data_dir / "input.pdf")]) == SUCCESS

    changed = json.loads(capsys.readouterr().out)
    assert changed == [
        {"FieldName": "Lastname", "DA": "/DejaVuSansMonoBook 0 Tf 0 g"},
        {"FieldName": "Firstname", "DA": "/DejaVuSansMonoBook 0 Tf 0 g"},
    ]

    doc = pymupdf.open(output_pdf_path)
    acroform = int(doc.xref_get_key(doc.pdf_catalog(), "AcroForm")[1].split()[0])
    font = int(doc.xref_get_key(acroform, "DR/Font/DejaVuSansMonoBook")[1].split()[0])
    assert doc.xref_get_key(font, "Subtype") == ("name", "/TrueType")
    assert doc.xref_get_key(font, "FontDescriptor/FontFile2")[0] == "xref"


def test_name_size_and_fields(test_data_dir, font_path, output_pdf_path, capsys):
    """--name, --size and --fields limit and shape the change"""
    argv = ["-fjson", "--font", font_path, "--name", "Mono", "--size", "9.5"]
    argv += ["--fields", "Firstname", "-o", str(output_pdf_path), str(test_data_dir / "input.pdf")]
    assert cli.main(["embed_font"] + argv) == SUCCESS

    assert json.loads(capsys.readouterr().out) == [
        {"FieldName": "Firstname", "DA": "/Mono 9.5 Tf 0 g"}
    ]
    doc = pymupdf.open(output_pdf_path)
    das = {w.field_name: doc.xref_get_key(w.xref, "DA")[1] for w in doc[0].widgets()}
    assert das["Lastname"].startswith("/Helv")


def test_unknown_field(test_data_dir, font_path, output_pdf_path):
    """a field name that is not a text field of the form is an error, and nothing is written"""
    argv = ["--font", font_path, "--fields", "Lastname,Nope", "-o", str(output_pdf_path)]
    assert cli.main(["embed_font"] + argv + [str(test_data_dir / "input.pdf")]) == ERROR_ENCOUNTERED
    assert not output_pdf_path.exists()


def test_not_a_font(test_data_dir, output_pdf_path):
    """a file that is not a TrueType font is refused"""
    pdf = str(test_data_dir / "input.pdf")
    argv = ["--font", pdf, "-o", str(output_pdf_path), pdf]
    assert cli.main(["embed_font"] + argv) == ERROR_ENCOUNTERED
    assert not output_pdf_path.exists()
