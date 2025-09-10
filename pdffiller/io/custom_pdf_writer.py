from pypdf import PageObject, PdfWriter
from pypdf.constants import AnnotationDictionaryAttributes as AA
from pypdf.constants import CatalogDictionary
from pypdf.constants import FieldDictionaryAttributes as FA
from pypdf.constants import InteractiveFormDictEntries
from pypdf.constants import PageAttributes as PG
from pypdf.errors import PyPdfError
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    RectangleObject,
    TextStringObject,
)

from ..typing import cast, Dict, List, Optional, Tuple, Union
from .output import PdfFillerOutput


class CustomPdfWriter(PdfWriter):  # pylint: disable=abstract-method
    """Overwrite PdfWriter to by-pass the related to flatten mode."""

    def update_field_values(
        self,
        page: Union[PageObject, List[PageObject], None],
        fields: Dict[str, Union[str, List[str], Tuple[str, str, float]]],
        flags: FA.FfBits = PdfWriter.FFBITS_NUL,
        auto_regenerate: Optional[bool] = True,
        flatten: bool = False,
    ) -> None:
        """
        Update the form field values for a given page from a fields dictionary.

        Copy field texts and values from fields to page.
        If the field links to a parent object, add the information to the parent.

        Args:
            page: `PageObject` - references **PDF writer's page** where the
                annotations and field data will be updated.
                `List[Pageobject]` - provides list of pages to be processed.
                `None` - all pages.
            fields: a Python dictionary of:

                * field names (/T) as keys and text values (/V) as value
                * field names (/T) as keys and list of text values (/V) for multiple choice list
                * field names (/T) as keys and tuple of:
                    * text values (/V)
                    * font id (e.g. /F1, the font id must exist)
                    * font size (0 for autosize)

            flags: A set of flags from :class:`~pypdf.constants.FieldDictionaryAttributes.FfBits`.

            auto_regenerate: Set/unset the need_appearances flag;
                the flag is unchanged if auto_regenerate is None.

            flatten: Whether or not to flatten the annotation. If True, this adds the annotation's
                appearance stream to the page contents. Note that this option does not remove the
                annotation itself.

        """
        if CatalogDictionary.ACRO_FORM not in self._root_object:
            raise PyPdfError("No /AcroForm dictionary in PDF of PdfWriter Object")
        af = cast(DictionaryObject, self._root_object[CatalogDictionary.ACRO_FORM])
        if InteractiveFormDictEntries.Fields not in af:
            raise PyPdfError("No /Fields dictionary in PDF of PdfWriter Object")
        if isinstance(auto_regenerate, bool):
            self.set_need_appearances_writer(auto_regenerate)
        # Iterate through pages, update field values
        if page is None:
            page = list(self.pages)
        if isinstance(page, list):
            for p in page:
                if PG.ANNOTS in p:  # just to prevent warnings
                    self.update_field_values(p, fields, flags, None, flatten=flatten)
            return
        output = PdfFillerOutput()
        if PG.ANNOTS not in page:
            output.warning(f"No fields to update on this page {__name__}")
            return
        for annotation in page[PG.ANNOTS]:  # type: ignore
            annotation = cast(DictionaryObject, annotation.get_object())
            if annotation.get("/Subtype", "") != "/Widget":
                continue
            if "/FT" in annotation and "/T" in annotation:
                parent_annotation = annotation
            else:
                parent_annotation = annotation.get(PG.PARENT, DictionaryObject()).get_object()

            for field, value in fields.items():
                if not (
                    self._get_qualified_field_name(parent_annotation) == field
                    or parent_annotation.get("/T", None) == field
                ):
                    continue
                if parent_annotation.get("/FT", None) == "/Ch" and "/I" in parent_annotation:
                    del parent_annotation["/I"]
                if flags:
                    annotation[NameObject(FA.Ff)] = NumberObject(flags)
                if not (
                    value is None and flatten
                ):  # Only change values if given by user and not flattening.
                    if isinstance(value, list):
                        lst = ArrayObject(TextStringObject(v) for v in value)
                        parent_annotation[NameObject(FA.V)] = lst
                    elif isinstance(value, tuple):
                        annotation[NameObject(FA.V)] = TextStringObject(
                            value[0],
                        )
                    else:
                        parent_annotation[NameObject(FA.V)] = TextStringObject(value)
                if parent_annotation.get(FA.FT) == "/Btn":
                    # Checkbox button (no /FT found in Radio widgets)
                    v = NameObject(value)
                    ap = cast(DictionaryObject, annotation[NameObject(AA.AP)])
                    normal_ap = cast(DictionaryObject, ap["/N"])
                    exist = True
                    if v not in normal_ap:
                        v = NameObject("/Off")
                        exist = False
                    appearance_stream_obj = normal_ap.get(v)
                    # other cases will be updated through the for loop
                    annotation[NameObject(AA.AS)] = v
                    annotation[NameObject(FA.V)] = v
                    if flatten and appearance_stream_obj is not None and exist:
                        # We basically copy the entire appearance stream, which should be
                        # an XObject that is already registered. No need to add font resources.
                        rct = cast(RectangleObject, annotation[AA.Rect])
                        self._add_apstream_object(
                            page, appearance_stream_obj, field, rct[0], rct[1]
                        )
                elif parent_annotation.get(FA.FT) == "/Tx" or parent_annotation.get(FA.FT) == "/Ch":
                    # textbox
                    if isinstance(value, tuple):
                        self._update_field_annotation(
                            page, parent_annotation, annotation, value[1], value[2], flatten=flatten
                        )
                    else:
                        self._update_field_annotation(
                            page, parent_annotation, annotation, flatten=flatten
                        )
                elif annotation.get(FA.FT) == "/Sig":  # deprecated  # not implemented yet
                    output.warning(f"Signature forms not implemented yet {__name__}")
