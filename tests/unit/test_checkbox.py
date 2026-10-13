import pymupdf
import pytest

from pdffiller.pdf import Pdf


@pytest.mark.parametrize(
    "value,checked",
    [
        (True, True),
        ("On", True),
        ("Oui", True),
        ("X", True),
        (False, False),
        (None, False),
        ("", False),
        ("Off", False),
        ("off", False),
        (" ", False),
        ("  ", False),
        (" Off", False),
        ("Off ", False),
    ],
)
def test_checkbox_value(test_data_dir, output_pdf_path, value, checked):
    """any value checks the box, except an empty one or Off, blanks around it included"""
    Pdf().fill(
        str(test_data_dir / "input.pdf"), str(output_pdf_path), {"Men": value}, flatten=False
    )

    doc = pymupdf.open(output_pdf_path)
    men = next(w for w in doc[0].widgets() if w.field_name == "Men")
    assert (doc.xref_get_key(men.xref, "AS")[1] != "/Off") is checked
