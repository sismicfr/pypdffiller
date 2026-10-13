import pymupdf
import pytest

from pdffiller.fonts import embed_font, field_da, MULTILINE, set_da_font
from pdffiller.pdf import Pdf

FONT = "DejaVuSansMonoBook"


@pytest.fixture(name="font_path")
def fixture_font_path(test_data_dir):
    return str(test_data_dir / "fonts" / "DejaVuSansMono.ttf")


@pytest.fixture(name="embedded_pdf")
def fixture_embedded_pdf(test_data_dir, font_path, tmp_path):
    """input.pdf with the test font embedded, and used by the Lastname field only"""
    path = tmp_path / "embedded.pdf"
    Pdf().embed_font(str(test_data_dir / "input.pdf"), str(path), font_path, fields=["Lastname"])
    return path


def spans(path):
    """The text drawn on the first page, with its font, out of the static labels of the form"""
    doc = pymupdf.open(path)
    # get_text() does not read the appearances of a form that is not flattened.
    doc.bake(annots=False)
    result = []
    for block in doc[0].get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                if "Aptos" not in span["font"]:
                    result.append((span["text"], span["font"], span["bbox"]))
    return result


def fonts_of(path):
    return {text: font for text, font, _ in spans(path)}


@pytest.mark.parametrize("flatten", [True, False])
def test_fill_draws_with_the_embedded_font(embedded_pdf, output_pdf_path, flatten):
    """the value of a field whose /DA names an embedded font is drawn with that font"""
    data = {"Lastname": "Éléonore œ €", "Firstname": "Jean"}
    Pdf().fill(str(embedded_pdf), str(output_pdf_path), data, flatten=flatten)

    assert fonts_of(output_pdf_path) == {"Éléonore œ €": FONT, "Jean": "Helvetica"}


def test_fill_keeps_the_da_and_the_value(embedded_pdf, output_pdf_path):
    """an interactive form keeps the font in /DA for the viewer, and /V holds the value"""
    Pdf().fill(str(embedded_pdf), str(output_pdf_path), {"Lastname": "Doe"}, flatten=False)

    doc = pymupdf.open(output_pdf_path)
    lastname = next(w for w in doc[0].widgets() if w.field_name == "Lastname")
    assert field_da(doc, lastname) == "/DejaVuSansMonoBook 0 Tf 0 g"
    assert lastname.field_value == "Doe"
    assert doc.xref_get_key(doc.pdf_catalog(), "AcroForm/NeedAppearances")[0] == "null"


def test_fill_keeps_the_checkboxes(test_data_dir, embedded_pdf, output_pdf_path, tmp_path):
    """the font only changes the text fields: the checkboxes and radio buttons look the same"""
    data = {"Lastname": "Doe", "Men": "On", "MaritalStatus": "Married"}
    reference = tmp_path / "reference.pdf"
    Pdf().fill(str(test_data_dir / "input.pdf"), str(reference), data)
    Pdf().fill(str(embedded_pdf), str(output_pdf_path), data)

    form = pymupdf.open(str(test_data_dir / "input.pdf"))[0]
    rects = [w.rect for w in form.widgets() if w.field_type_string in ("CheckBox", "RadioButton")]
    assert len(rects) == 5

    def buttons(path):
        page = pymupdf.open(path)[0]
        return [page.get_pixmap(clip=rect).samples for rect in rects]

    assert buttons(output_pdf_path) == buttons(reference)


def test_fill_falls_back_when_a_glyph_is_missing(embedded_pdf, output_pdf_path, capsys):
    """a character that the font cannot draw keeps the default rendering, with a warning"""
    Pdf().fill(str(embedded_pdf), str(output_pdf_path), {"Lastname": "Ŵales"})

    # Helvetica draws the Ŵ as a dot, as it did before the embedded fonts.
    assert list(fonts_of(output_pdf_path).values()) == ["Helvetica"]
    assert "cannot draw 'Ŵ'" in capsys.readouterr().err


def test_fill_ignores_a_font_that_is_not_embedded(test_data_dir, output_pdf_path):
    """a /DA font of /DR without a font file keeps the default rendering"""
    source = pymupdf.open(str(test_data_dir / "input.pdf"))
    for widget in source[0].widgets():
        if widget.field_name == "Lastname":
            source.xref_set_key(widget.xref, "DA", "(/Arial 0 Tf 0 g)")
    path = output_pdf_path.with_suffix(".source.pdf")
    source.save(path)

    Pdf().fill(str(path), str(output_pdf_path), {"Lastname": "Doe"})
    assert fonts_of(output_pdf_path) == {"Doe": "Helvetica"}


def test_embed_rewrites_a_filled_field(test_data_dir, font_path, output_pdf_path, tmp_path):
    """a field that already holds a value shows it with the new font"""
    filled = tmp_path / "filled.pdf"
    Pdf().fill(str(test_data_dir / "input.pdf"), str(filled), {"Lastname": "Doe"}, flatten=False)
    Pdf().embed_font(str(filled), str(output_pdf_path), font_path)

    assert fonts_of(output_pdf_path) == {"Doe": FONT}


def test_multiline_and_alignment(test_data_dir, font_path, output_pdf_path, tmp_path):
    """a multiline field wraps its words, and /Q 2 aligns the lines on the right"""
    doc = pymupdf.open(str(test_data_dir / "input.pdf"))
    embed_font(doc, font_path, "Mono")
    for widget in doc[0].widgets():
        if widget.field_name == "Lastname":
            rect = widget.rect
            doc.xref_set_key(widget.xref, "DA", pymupdf.get_pdf_str(set_da_font("", "Mono", 6)))
            doc.xref_set_key(widget.xref, "Ff", str(MULTILINE))
            doc.xref_set_key(widget.xref, "Q", "2")
    source = tmp_path / "multiline.pdf"
    doc.save(source)

    value = "one two three four five six seven eight nine ten eleven twelve"
    Pdf().fill(str(source), str(output_pdf_path), {"Lastname": value})

    lines = [(text, bbox) for text, font, bbox in spans(output_pdf_path) if font == FONT]
    assert len(lines) > 1
    assert " ".join(text.strip() for text, _ in lines) == value
    for _, bbox in lines:
        assert bbox[2] == pytest.approx(rect.x1 - 2, abs=1)
        assert rect.y0 <= bbox[1] and bbox[3] <= rect.y1 + 1
