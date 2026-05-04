"""
A module for wrapping PDF form operations, providing a high-level interface
for filling, and manipulating PDF forms.

This module simplifies common tasks such as:
- Filling PDF forms with data from a dictionary.
- Fetching PDF forms fields

The core class, `Pdf`, encapsulates a PDF document and provides
methods for interacting with its form fields and content.
"""

from collections import OrderedDict

import pymupdf

from pdffiller.exceptions import PdfFillerException
from pdffiller.io.output import PdfFillerOutput

from .typing import Any, cast, Dict, List, Optional, PathLike, StreamType, Type
from .widgets.base import Widget
from .widgets.checkbox import CheckBoxWidget
from .widgets.radio import RadioWidget
from .widgets.text import TextWidget


class PdfAttributes:  # pylint: disable=too-few-public-methods
    """Various constants, enums, and flags to aid readability."""

    READ_ONLY = 1 << 0


class Pdf:
    """
    A class to wrap PDF form operations, providing a simplified interface
    for common tasks such as filling, creating, and manipulating PDF forms.

    The `Pdf` class encapsulates a PDF document and provides methods
    for interacting with its form fields (widgets) and content.

    """

    TYPE_TO_OBJECT: Dict[str, Type[Widget]] = {
        "Text": TextWidget,
        "RadioButton": RadioWidget,
        "CheckBox": CheckBoxWidget,
    }

    def __init__(
        self, filename: Optional[PathLike] = None, stream: Optional[StreamType] = None
    ) -> None:
        """
        Constructor method for the `Pdf` class.

        Initializes a new `Pdf` object with the given template PDF and optional keyword arguments.

        Args:
            filename (Optional[PathLike]): Path to the input pdf
            stream (Optional[StreamType]): An open file-like object containing the PDF data.
        """

        super().__init__()
        self.widgets: OrderedDict[str, Widget] = OrderedDict()
        self._init_helper(filename, stream)

    def _init_helper(
        self, filename: Optional[PathLike] = None, stream: Optional[StreamType] = None
    ) -> None:
        """
        Helper method to initialize widgets

        Args:
            filename (Optional[PathLike]): Path to the input pdf
            stream (Optional[StreamType]): An open file-like object containing the PDF data.
        """
        if not filename and not stream:
            return

        output = PdfFillerOutput()
        output.info("loading file in memory")
        loaded_widgets: OrderedDict[str, Widget] = OrderedDict()
        try:
            doc = pymupdf.open(filename=filename, stream=stream)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            PdfFillerOutput().error(str(ex))
            raise PdfFillerException(
                f"failed to load {filename or 'file from input string'}"
            ) from ex

        for i, page in enumerate(doc.pages()):
            output.verbose(f"loading page {i + 1}/{doc.page_count}")
            for widget in page.widgets():
                button_states = widget.button_states()
                choices = button_states["normal"] if button_states else None

                if widget.field_name not in loaded_widgets:
                    if widget.field_type_string not in self.TYPE_TO_OBJECT:
                        output.verbose(f"unsupported {widget.field_type_string} widget type")
                        continue
                    new_widget = self.TYPE_TO_OBJECT[widget.field_type_string](
                        widget.field_name, i, widget.field_value, widget.field_flags & (1 << 0)
                    )
                    if choices and isinstance(new_widget, CheckBoxWidget):
                        if "Off" not in choices:
                            choices.insert(0, "Off")
                        new_widget.choices = [choice.replace("#20", " ") for choice in choices]
                    elif isinstance(new_widget, TextWidget):
                        new_widget.max_length = self._resolve_text_maxlen(doc, widget)
                    loaded_widgets[widget.field_name] = new_widget
                else:
                    new_widget = loaded_widgets[widget.field_name]
                    if choices and isinstance(new_widget, CheckBoxWidget):
                        for each in choices:
                            each = each.replace("#20", " ")
                            if new_widget.choices is not None:
                                if each not in new_widget.choices:
                                    new_widget.choices.append(each)
                            else:
                                new_widget.choices = [each]

                        cast(CheckBoxWidget, loaded_widgets[widget.field_name]).choices = (
                            new_widget.choices
                        )
                        if "Off" != widget.field_value:
                            cast(CheckBoxWidget, loaded_widgets[widget.field_name]).value = (
                                widget.field_value
                            )

        self.widgets = loaded_widgets

    @staticmethod
    def _resolve_text_maxlen(doc: pymupdf.Document, widget: Any) -> Optional[int]:
        """
        Resolve the MaxLen value for a text widget by walking up the PDF object hierarchy.

        PyMuPDF's widget.text_maxlen may not reflect the actual MaxLen when it is
        defined on a parent field dictionary rather than on the widget annotation itself.
        This method checks the widget xref and its parents for /MaxLen.

        Args:
            doc: The pymupdf Document.
            widget: The pymupdf Widget.

        Returns:
            The resolved max length, or None if not found.
        """
        max_length: Optional[int] = widget.text_maxlen
        xref = widget.xref
        while xref > 0:
            key_type, value = doc.xref_get_key(xref, "MaxLen")
            if key_type != "null" and value:
                try:
                    int_value = int(value)
                    if max_length is None or max_length < int_value:
                        max_length = int_value
                    # return int(value)
                except (ValueError, TypeError):
                    pass
            # Walk up to parent
            key_type, value = doc.xref_get_key(xref, "Parent")
            if key_type == "xref":
                parent_xref = int(value.split()[0])
                if parent_xref == xref:
                    break
                xref = parent_xref
            else:
                break

        return max_length

    COMB_FLAG = 1 << 24  # Bit 25 in PDF spec (Comb option)

    @staticmethod
    def _has_comb_flag(doc: pymupdf.Document, widget: Any) -> bool:
        """
        Check if the Comb flag is set on the widget or any of its parents.

        Args:
            doc: The pymupdf Document.
            widget: The pymupdf Widget.

        Returns:
            True if the Comb flag is set on any node in the hierarchy.
        """
        xref = widget.xref
        while xref > 0:
            key_type, ff_value = doc.xref_get_key(xref, "Ff")
            if key_type != "null" and ff_value:
                try:
                    if int(ff_value) & Pdf.COMB_FLAG:
                        return True
                except (ValueError, TypeError):
                    pass
            key_type, value = doc.xref_get_key(xref, "Parent")
            if key_type == "xref":
                parent_xref = int(value.split()[0])
                if parent_xref == xref:
                    break
                xref = parent_xref
            else:
                break
        return False

    @staticmethod
    def _remove_maxlen(doc: pymupdf.Document, widget: Any, deep: bool = False) -> None:
        """
        Remove /MaxLen from the widget and all its parent field dictionaries.

        In deep mode, also clears the Comb flag (bit 25 of /Ff).
        In normal mode, /MaxLen is only removed on nodes where Comb is not set.

        Args:
            doc: The pymupdf Document.
            widget: The pymupdf Widget.
            deep: If True, also clear the Comb flag from /Ff.
        """
        xref = widget.xref
        while xref > 0:
            # Check Comb flag on this node
            has_comb = False
            key_type, ff_value = doc.xref_get_key(xref, "Ff")
            if key_type != "null" and ff_value:
                try:
                    flags = int(ff_value)
                    has_comb = bool(flags & Pdf.COMB_FLAG)
                except (ValueError, TypeError):
                    pass

            if deep:
                # Deep mode: remove /MaxLen and clear Comb flag
                if doc.xref_get_key(xref, "MaxLen")[0] != "null":
                    doc.xref_set_key(xref, "MaxLen", "null")
                if has_comb:
                    doc.xref_set_key(xref, "Ff", str(flags & ~Pdf.COMB_FLAG))
            else:
                # Normal mode: only remove /MaxLen if Comb is not set on this node
                if not has_comb and doc.xref_get_key(xref, "MaxLen")[0] != "null":
                    doc.xref_set_key(xref, "MaxLen", "null")

            # Walk up to parent
            key_type, value = doc.xref_get_key(xref, "Parent")
            if key_type == "xref":
                parent_xref = int(value.split()[0])
                if parent_xref == xref:
                    break
                xref = parent_xref
            else:
                break
        widget.text_maxlen = 0

    def sanitize(
        self,
        input_file: PathLike,
        output_file: PathLike,
        deep: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Sanitize a PDF by removing /MaxLen constraints from all text fields.

        This fixes PDFs where /MaxLen is set incorrectly (e.g. 4 instead of 27),
        which causes text truncation when filling the form.

        Args:
            input_file (PathLike): The input file path.
            output_file (PathLike): The output file path.
            deep: If True, also clear the Comb flag from /Ff.

        Returns:
            A list of dicts describing each sanitized field:
            [{"FieldName": ..., "FieldType": "text", "MaxLen": <old_value>}, ...]
        """
        try:
            document = pymupdf.open(filename=input_file)
        except Exception as ex:
            PdfFillerOutput().error(str(ex))
            raise PdfFillerException(f"failed to open {input_file}") from ex

        output = PdfFillerOutput()
        output.info("sanitizing pdf text fields")

        sanitized: List[Dict[str, Any]] = []
        for page in document:
            for field in page.widgets():
                if (
                    field.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT  # pylint: disable=no-member
                    and field.text_maxlen
                ):
                    # Skip fields with Comb flag in normal mode
                    if not deep and self._has_comb_flag(document, field):
                        output.verbose(f"skipping {field.field_name} (Comb flag active)")
                        continue
                    old_maxlen = field.text_maxlen
                    output.verbose(f"removing MaxLen={old_maxlen} from {field.field_name}")
                    self._remove_maxlen(document, field, deep)
                    field.update()
                    sanitized.append(
                        {
                            "FieldName": field.field_name,
                            "FieldType": field.field_type_string,
                            "MaxLen": old_maxlen,
                        }
                    )

        try:
            document.save(output_file)
        except Exception:  # pylint: disable=broad-exception-caught
            output.warning("an error occurs when saving file")

        return sanitized

    @property
    def schema(self) -> List[Dict[str, Any]]:
        """
        Returns the JSON schema of the PDF form, describing the structure and data
        types of the form fields.

        This schema can be used to generate user interfaces or validate data before
        filling the form.

        Returns:
            dict: A dictionary representing the JSON schema of the PDF form.
        """

        return [widget.schema_definition for widget in self.widgets.values()]

    def fill(
        self,
        input_file: PathLike,
        output_file: PathLike,
        data: Dict[str, str],
        flatten: bool = True,
    ) -> "Pdf":
        """
        Fill the PDF form with data from a dictionary.

        Args:
            input_file (PathLike): The input file path.
            output_file (PathLike): The output file path.
            data (Dict[str, Union[str, bool, int]]): A dictionary where keys are form field names
                and values are the data to fill the fields with.  Values can be strings, booleans,
                or integers.
            flatten (bool): Whether to flatten the form after filling, making the fields read-only
                (default: False).

        Returns:
            Pdf: The `Pdf` object, allowing for method chaining.
        """
        try:
            document = pymupdf.open(filename=input_file)
        except Exception as ex:
            PdfFillerOutput().error(str(ex))
            raise PdfFillerException(f"failed to open {input_file}") from ex

        output = PdfFillerOutput()

        output.info("filling pdf with input values")
        for page in document:
            for field in page.widgets():
                if (
                    field.field_type
                    == pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON  # pylint: disable=no-member
                ):
                    field.field_value = None
        # Iterate over all pages and process fields
        for page in document:
            for field in page.widgets():
                if field.field_name in data:
                    value = data[field.field_name]

                    # Handling checkboxes
                    if (
                        field.field_type
                        == pymupdf.PDF_WIDGET_TYPE_CHECKBOX  # pylint: disable=no-member
                    ):
                        value = value.replace(" ", "#20")
                        if value.strip() and "off" != value.strip().lower():
                            output.verbose(
                                f"updating checkbox with {value} from {field.field_value}"
                            )
                            field.field_value = True
                        else:
                            field.field_value = False

                    # Handling radio buttons
                    elif (
                        field.field_type
                        == pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON  # pylint: disable=no-member
                    ):
                        value = value.replace(" ", "#20")
                        if value.lower() == field.on_state().lower():
                            output.verbose(
                                f"updating radiobutton with {value} from {field.field_value}"
                            )
                            field.field_value = value
                        else:
                            continue

                    # Handling other fields types
                    else:
                        # Remove MaxLen constraint from the PDF object to avoid truncation
                        self._remove_maxlen(document, field)
                        output.verbose(
                            f"updating {field.field_name} with {value} from {field.field_value}"
                        )
                        field.field_value = value
                    # Update the widget!
                    field.update()
        try:
            if flatten:
                output.info("remove all annotations")
                document.bake(annots=False)

            # Save the modified PDF
            document.save(output_file)
        except Exception:  # pylint: disable=broad-exception-caught
            output.warning("an error occurs when saving file")

        return self
