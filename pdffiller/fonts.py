"""
Embedded fonts for form fields.

PyMuPDF and MuPDF only draw a field appearance with one of the base 14 fonts:
whatever the /DA of a field names, ``Widget.update()`` writes ``/Helv`` back
and draws Helvetica. To make a field use another font, the font file is
embedded in the AcroForm resources (/DR) and the appearance stream of the
field is written here, with that font.

The font is embedded as a simple TrueType font in WinAnsiEncoding, not as a
Type0 font: a viewer that regenerates the appearance when a human types in the
field (Acrobat, poppler) reads the font from /DR, and simple fonts are the
form that every viewer supports there. The cost is the character set: a value
with a character out of WinAnsi (cp1252) keeps the base 14 rendering.

``NeedAppearances`` is never set: it makes the viewer regenerate the
appearance of every field, and poppler then draws no checkbox at all.
"""

import re

import pymupdf

from pdffiller.exceptions import PdfFillerException

from .typing import Dict, List, Optional, Tuple

# Field flag of a multiline text field, PDF 32000-1:2008 table 228.
MULTILINE = 1 << 12

# The standard fonts of /DA. They are never embedded, and MuPDF already draws them.
BASE14_NAMES = {"Helv", "HeBo", "TiRo", "TiBo", "Cour", "CoBo", "ZaDb", "Symb"}

# Horizontal padding of the text inside the border, the value MuPDF and Acrobat use.
PADDING = 2.0

# Font size used for a multiline field with an automatic size (0 Tf), before
# shrinking it to fit, as Acrobat does.
AUTO_MULTILINE_SIZE = 12.0
MIN_AUTO_SIZE = 4.0

DA_FONT = re.compile(r"/([^\s/\[\]()<>{}%]+)\s+(-?[\d.]+)\s+Tf")


class EmbeddedFont:  # pylint: disable=too-few-public-methods
    """A font of /DR whose file is embedded, with the metrics to lay out text."""

    def __init__(self, name: str, xref: int, font: pymupdf.Font):
        self.name = name
        self.xref = xref
        self.font = font

    def missing(self, text: str) -> str:
        """
        Return the characters of a text that the font cannot draw.

        A font that a PDF editor embedded is often a subset, which only holds
        the glyphs of the text it was made for. A character out of WinAnsi is
        missing too, because the text is written in that encoding.
        """
        missing = []
        for char in dict.fromkeys(text):
            if char in "\r\n":
                continue
            try:
                char.encode("cp1252")
            except UnicodeEncodeError:
                missing.append(char)
                continue
            if not self.font.has_glyph(ord(char)):
                missing.append(char)
        return "".join(missing)


def pdf_name(value: str) -> str:
    """Make a string usable as a PDF name: letters, digits, dash and underscore only."""
    name = re.sub(r"[^A-Za-z0-9_-]", "", value)
    if not name:
        raise PdfFillerException(f"cannot make a font resource name from '{value}'")
    return name


def _ref(value: Tuple[str, str]) -> Optional[int]:
    kind, text = value
    if kind != "xref":
        return None
    return int(text.split()[0])


def _acroform(doc: pymupdf.Document) -> int:
    """Return the xref of the AcroForm dictionary, made indirect if it is inline."""
    catalog = doc.pdf_catalog()
    value = doc.xref_get_key(catalog, "AcroForm")
    xref = _ref(value)
    if xref is not None:
        return xref
    if value[0] != "dict":
        raise PdfFillerException("the document has no form")
    xref = doc.get_new_xref()
    doc.update_object(xref, value[1])
    doc.xref_set_key(catalog, "AcroForm", f"{xref} 0 R")
    return xref


def _winansi_widths(font: pymupdf.Font) -> List[int]:
    widths = []
    for code in range(32, 256):
        try:
            char = bytes([code]).decode("cp1252")
        except UnicodeDecodeError:
            widths.append(0)
            continue
        widths.append(round(font.glyph_advance(ord(char)) * 1000))
    return widths


def embed_font(doc: pymupdf.Document, font_path: str, name: str) -> int:
    """
    Embed a TrueType font file and declare it in the AcroForm resources.

    The whole file is embedded, not a subset: the characters that a field
    will receive are not known when the form is prepared.

    Returns:
        The xref of the font dictionary.
    """
    try:
        font = pymupdf.Font(fontfile=font_path)
        with open(font_path, "rb") as stream:
            data = stream.read()
    except Exception as exc:
        raise PdfFillerException(f"cannot read the font file {font_path}") from exc
    if data[:4] not in (b"\x00\x01\x00\x00", b"true"):
        raise PdfFillerException(f"{font_path} is not a TrueType font file")

    base_font = pdf_name(font.name)
    file_xref = doc.get_new_xref()
    doc.update_object(file_xref, f"<</Length1 {len(data)}>>")
    doc.update_stream(file_xref, data)

    bbox = font.bbox
    descriptor = doc.get_new_xref()
    doc.update_object(
        descriptor,
        f"<</Type/FontDescriptor/FontName/{base_font}/Flags 32"
        f"/FontBBox[{round(bbox.x0 * 1000)} {round(bbox.y0 * 1000)}"
        f" {round(bbox.x1 * 1000)} {round(bbox.y1 * 1000)}]"
        f"/ItalicAngle 0/Ascent {round(font.ascender * 1000)}"
        f"/Descent {round(font.descender * 1000)}/CapHeight {round(font.ascender * 1000)}"
        f"/StemV 80/FontFile2 {file_xref} 0 R>>",
    )

    font_xref = doc.get_new_xref()
    widths = " ".join(str(width) for width in _winansi_widths(font))
    doc.update_object(
        font_xref,
        f"<</Type/Font/Subtype/TrueType/BaseFont/{base_font}/FirstChar 32/LastChar 255"
        f"/Widths[{widths}]/Encoding/WinAnsiEncoding/FontDescriptor {descriptor} 0 R>>",
    )

    doc.xref_set_key(_acroform(doc), f"DR/Font/{name}", f"{font_xref} 0 R")
    return int(font_xref)


class FontResolver:
    """Find the embedded font that the /DA of a field names, if there is one."""

    def __init__(self, doc: pymupdf.Document):
        self.doc = doc
        self._cache: Dict[str, Optional[EmbeddedFont]] = {}

    def resolve(self, da: str) -> Optional[EmbeddedFont]:
        """Return the embedded font of a /DA string, or None to keep the PyMuPDF rendering."""
        match = DA_FONT.search(da)
        if not match or match.group(1) in BASE14_NAMES:
            return None
        name = match.group(1)
        if name not in self._cache:
            self._cache[name] = self._load(name)
        return self._cache[name]

    def _load(self, name: str) -> Optional[EmbeddedFont]:
        acroform = _ref(self.doc.xref_get_key(self.doc.pdf_catalog(), "AcroForm"))
        if acroform is None:
            return None
        xref = _ref(self.doc.xref_get_key(acroform, f"DR/Font/{name}"))
        if xref is None:
            return None
        # The text is written as WinAnsi bytes, so a font with another
        # encoding (a symbolic font, /Differences) would show other glyphs.
        if self.doc.xref_get_key(xref, "Subtype")[1] != "/TrueType":
            return None
        if self.doc.xref_get_key(xref, "Encoding")[1] != "/WinAnsiEncoding":
            return None
        if _ref(self.doc.xref_get_key(xref, "FontDescriptor/FontFile2")) is None:
            return None
        _, _, _, buffer = self.doc.extract_font(xref)
        if not buffer:
            return None
        return EmbeddedFont(name, xref, pymupdf.Font(fontbuffer=buffer))


def set_da_font(da: str, name: str, size: Optional[float] = None) -> str:
    """Return a /DA that uses the font ``name``, at ``size`` or at the size of the old /DA."""
    match = DA_FONT.search(da)
    if size is None:
        size = float(match.group(2)) if match else 0.0
    colour = DA_FONT.sub("", da).strip() or "0 g"
    return f"/{name} {size:g} Tf {colour}"


def field_da(doc: pymupdf.Document, widget: pymupdf.Widget) -> str:
    """Return the /DA of a field, inherited from its parent or from the AcroForm."""
    xref = widget.xref
    while xref:
        kind, value = doc.xref_get_key(xref, "DA")
        if kind == "string":
            return str(value)
        xref = _ref(doc.xref_get_key(xref, "Parent")) or 0
    acroform = _ref(doc.xref_get_key(doc.pdf_catalog(), "AcroForm"))
    if acroform is not None:
        kind, value = doc.xref_get_key(acroform, "DA")
        if kind == "string":
            return str(value)
    return ""


def _inherited(doc: pymupdf.Document, xref: int, key: str) -> Tuple[str, str]:
    while xref:
        kind, value = doc.xref_get_key(xref, key)
        if kind != "null":
            return str(kind), str(value)
        xref = _ref(doc.xref_get_key(xref, "Parent")) or 0
    return ("null", "null")


def _encode(text: str) -> bytes:
    raw = text.encode("cp1252", errors="replace")
    return raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _wrap(font: pymupdf.Font, text: str, size: float, width: float) -> List[str]:
    lines: List[str] = []
    for paragraph in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = ""
        for word in paragraph.split(" "):
            candidate = f"{line} {word}" if line else word
            if line and font.text_length(candidate, size) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


def _colour(values: str, stroke: bool) -> str:
    """Write a /MK colour array as a colour operator."""
    parts = values.strip("[]").split()
    operator = {1: "g", 3: "rg", 4: "k"}.get(len(parts))
    if operator is None:
        return ""
    return f"{' '.join(parts)} {operator.upper() if stroke else operator}"


def _frame(
    doc: pymupdf.Document, xref: int, width: float, height: float
) -> Tuple[List[str], float]:
    """Draw the background and the border of /MK, and return the border width."""
    commands: List[str] = []
    _, background = doc.xref_get_key(xref, "MK/BG")
    if background.startswith("["):
        commands += [_colour(background, False), f"0 0 {width:g} {height:g} re f"]
    border = 0.0
    _, border_colour = doc.xref_get_key(xref, "MK/BC")
    if border_colour.startswith("["):
        kind, border_width = doc.xref_get_key(xref, "BS/W")
        border = float(border_width) if kind != "null" else 1.0
        commands += [
            _colour(border_colour, True),
            f"{border:g} w",
            f"{border / 2:g} {border / 2:g} {width - border:g} {height - border:g} re S",
        ]
    return commands, border


def _layout(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    font: pymupdf.Font,
    value: str,
    size: float,
    multiline: bool,
    width: float,
    height: float,
) -> Tuple[float, List[str]]:
    """Return the font size and the lines of a value in a box, for a size of 0 (automatic) too."""
    line_height = font.ascender - font.descender
    if not multiline:
        line = value.replace("\r", " ").replace("\n", " ")
        if size == 0:
            size = height / line_height * 0.9
            text_width = font.text_length(line, 1)
            if text_width * size > width > 0:
                size = max(MIN_AUTO_SIZE, width / text_width)
        return size, [line]
    if size != 0:
        return size, _wrap(font, value, size, width)
    size = AUTO_MULTILINE_SIZE
    lines = _wrap(font, value, size, width)
    while size > MIN_AUTO_SIZE and len(lines) * size * line_height > height:
        size -= 0.5
        lines = _wrap(font, value, size, width)
    return size, lines


def write_text_appearance(
    doc: pymupdf.Document,
    widget: pymupdf.Widget,
    font: EmbeddedFont,
    da: str,
    value: str,
) -> None:
    """
    Write the normal appearance of a text field with an embedded font.

    The layout follows what MuPDF does for the base 14 fonts: padding of 2
    points, the alignment of /Q, the automatic size of ``0 Tf``, and word
    wrap for a multiline field. A rotated field (/MK /R) is not supported.
    """
    xref = widget.xref
    width, height = widget.rect.width, widget.rect.height
    metrics = font.font
    match = DA_FONT.search(da)

    commands, border = _frame(doc, xref, width, height)
    multiline = bool(widget.field_flags & MULTILINE)
    size, lines = _layout(
        metrics,
        value,
        float(match.group(2)) if match else 0.0,
        multiline,
        width - 2 * (PADDING + border),
        height - 2 * border,
    )

    leading = size * (metrics.ascender - metrics.descender)
    if multiline:
        baseline = height - border - PADDING - metrics.ascender * size
    else:
        baseline = (height - leading) / 2 - metrics.descender * size
    _, alignment = _inherited(doc, xref, "Q")
    quadding = int(alignment) if alignment.isdigit() else 0

    commands += [
        f"{border:g} {border:g} {width - 2 * border:g} {height - 2 * border:g} re W n",
        "BT",
        DA_FONT.sub("", da).strip() or "0 g",
        f"/{font.name} {size:g} Tf",
    ]
    previous_x = 0.0
    for index, line in enumerate(lines):
        x = PADDING + border
        if quadding == 1:
            x = (width - metrics.text_length(line, size)) / 2
        elif quadding == 2:
            x = width - PADDING - border - metrics.text_length(line, size)
        commands.append(f"{x - previous_x:.3f} {baseline if index == 0 else -leading:.3f} Td")
        commands.append(f"({_encode(line).decode('latin-1')}) Tj")
        previous_x = x

    stream = "\n".join(["/Tx BMC", "q"] + [c for c in commands if c] + ["ET", "Q", "EMC"])
    appearance = doc.get_new_xref()
    doc.update_object(
        appearance,
        f"<</Type/XObject/Subtype/Form/BBox[0 0 {width:g} {height:g}]"
        f"/Resources<</Font<</{font.name} {font.xref} 0 R>>>>>>",
    )
    doc.update_stream(appearance, stream.encode("latin-1"))
    doc.xref_set_key(xref, "AP", f"<</N {appearance} 0 R>>")
