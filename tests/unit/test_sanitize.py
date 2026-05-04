import pytest

from pdffiller.pdf import Pdf


def test_sanitize_removes_maxlen(test_data_dir, output_pdf_path):
    """Test that sanitize removes MaxLen from text fields without Comb flag"""
    pdf = Pdf()
    sanitized = pdf.sanitize(
        str(test_data_dir / "input.pdf"),
        str(output_pdf_path),
    )

    # Verify output file was created
    assert output_pdf_path.exists()

    # Verify sanitized fields are text fields with a MaxLen value
    for field in sanitized:
        assert "FieldName" in field
        assert "FieldType" in field
        assert "MaxLen" in field
        assert field["FieldType"] == "Text"
        assert isinstance(field["MaxLen"], int)
        assert field["MaxLen"] > 0


def test_sanitize_output_has_no_maxlen(test_data_dir, output_pdf_path):
    """Test that the sanitized PDF has no MaxLen on non-Comb text fields"""
    pdf = Pdf()
    pdf.sanitize(
        str(test_data_dir / "input.pdf"),
        str(output_pdf_path),
    )

    # Re-read the sanitized PDF and check that text fields have no MaxLen
    sanitized_pdf = Pdf(str(output_pdf_path))
    for widget in sanitized_pdf.widgets.values():
        if hasattr(widget, "max_length") and not _has_comb_in_pdf(
            str(output_pdf_path), widget.name
        ):
            assert widget.max_length is None or widget.max_length == 0


def test_sanitize_deep_mode(test_data_dir, output_pdf_path):
    """Test that deep mode also processes fields with Comb flag"""
    pdf = Pdf()
    sanitized_normal = pdf.sanitize(
        str(test_data_dir / "input.pdf"),
        str(output_pdf_path),
    )

    # Deep mode should sanitize at least as many fields as normal mode
    output_pdf_path_deep = output_pdf_path.parent / "deep_output.pdf"
    pdf2 = Pdf()
    sanitized_deep = pdf2.sanitize(
        str(test_data_dir / "input.pdf"),
        str(output_pdf_path_deep),
        deep=True,
    )

    assert len(sanitized_deep) >= len(sanitized_normal)

    if output_pdf_path_deep.exists():
        output_pdf_path_deep.unlink()


def test_sanitize_returns_list(test_data_dir, output_pdf_path):
    """Test that sanitize returns a list"""
    pdf = Pdf()
    result = pdf.sanitize(
        str(test_data_dir / "input.pdf"),
        str(output_pdf_path),
    )
    assert isinstance(result, list)


def test_sanitize_invalid_pdf(test_data_dir, output_pdf_path):
    """Test that sanitize raises on invalid PDF"""
    from pdffiller.exceptions import PdfFillerException

    pdf = Pdf()
    with pytest.raises(PdfFillerException):
        pdf.sanitize(
            str(test_data_dir / "empty.pdf"),
            str(output_pdf_path),
        )


def _has_comb_in_pdf(pdf_path, field_name):
    """Helper to check if a field has Comb flag set"""
    import pymupdf

    doc = pymupdf.open(filename=pdf_path)
    for page in doc:
        for widget in page.widgets():
            if widget.field_name == field_name:
                return bool(widget.field_flags & Pdf.COMB_FLAG)
    return False
