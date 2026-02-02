import pytest

from pdffiller.pdf import Pdf
from pdffiller.exceptions import PdfFillerException


def test_valid_pdf(test_data_dir):
    reader = Pdf(str(test_data_dir / "input.pdf"))
    assert len(reader.widgets) == 5
    schema = reader.schema
    assert len(schema) == 5
    assert schema[0]["FieldName"] == "Lastname"
    assert schema[1]["FieldName"] == "Firstname"
    assert schema[2]["FieldName"] == "Men"
    assert schema[3]["FieldName"] == "Women"
    assert schema[4]["FieldName"] == "MaritalStatus"
    assert len(schema[4]["FieldOptions"]) == 4
    assert "Divorced" in schema[4]["FieldOptions"]
    assert "Off" in schema[4]["FieldOptions"]
    assert schema[4]["FieldValue"] == "Off"


def test_invalid_pdf(test_data_dir):
    with pytest.raises(PdfFillerException):
        Pdf(str(test_data_dir / "empty.pdf"))
