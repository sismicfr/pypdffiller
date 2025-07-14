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

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

from pdffiller.io.output import PdfFillerOutput

from .typing import (
    Any,
    Callable,
    cast,
    Dict,
    List,
    Optional,
    PathLike,
    StrByteType,
    Type,
    Union,
)
from .widgets.base import Widget
from .widgets.checkbox import CheckBoxWidget
from .widgets.radio import RadioWidget
from .widgets.text import TextWidget


class PdfAttributes:  # pylint: disable=too-few-public-methods
    """Various constants, enums, and flags to aid readability."""

    Widget = "/Widget"
    Subtype = "/Subtype"
    Parent = "/Parent"
    T = "/T"
    V = "/V"
    AS = "/AS"
    Kids = "/Kids"
    AP = "/AP"
    N = "/N"
    D = "/D"
    Opt = "/Opt"
    MaxLen = "/MaxLen"
    AcroForm = "/AcroForm"
    Root = "/Root"
    XFA = "/XFA"
    FT = "/FT"
    Ff = "/Ff"
    Tx = "/Tx"
    Ch = "/Ch"
    Btn = "/Btn"
    Off = "/Off"
    READ_ONLY = 1 << 0


class Pdf:
    """
    A class to wrap PDF form operations, providing a simplified interface
    for common tasks such as filling, creating, and manipulating PDF forms.

    The `Pdf` class encapsulates a PDF document and provides methods
    for interacting with its form fields (widgets) and content.

    """

    TYPE_TO_OBJECT: Dict[str, Type[Widget]] = {
        "text": TextWidget,
        "radio": RadioWidget,
        "checkbox": CheckBoxWidget,
    }

    def __init__(
        self,
        content: Optional[StrByteType] = None,
        adode_mode: Optional[bool] = True,
    ) -> None:
        """
        Constructor method for the `Pdf` class.

        Initializes a new `Pdf` object with the given template PDF and optional keyword arguments.

        Args:
            content (Optional[StrByteType]): The template PDF, provided as either:
                - str: The file path to the PDF.
                - BinaryIO: An open file-like object containing the PDF data.
            adobe_mode (bool): Whether to enable Adobe-specific compatibility mode.
        """

        super().__init__()
        self.widgets: OrderedDict[str, Widget] = OrderedDict()
        self.adobe_mode = adode_mode

        self._init_helper(content)

    def _init_helper(self, content: Optional[StrByteType] = None) -> None:
        """
        Helper method to initialize widgets

        This method is called during initialization and after certain operations
        that modify the PDF content.
        It rebuilds the widget dictionary.

        Args:
            content (Optional[StrByteType]): The template PDF, provided as either:
                - str: The file path to the PDF.
                - BinaryIO: An open file-like object containing the PDF data.
        """
        if not content:
            return

        loaded_widgets: OrderedDict[str, Widget] = OrderedDict()
        try:
            pdf_file = PdfReader(content)
        except PyPdfError as ex:
            PdfFillerOutput().error(str(ex))
            return

        for i, page in enumerate(pdf_file.pages):
            widgets: Optional[ArrayObject] = page.annotations
            if not widgets:
                continue
            for widget in widgets:
                choices: Optional[List[str]] = None
                if (
                    PdfAttributes.Subtype not in widget
                    or widget[PdfAttributes.Subtype] != PdfAttributes.Widget
                ):
                    continue

                if PdfAttributes.T not in widget:
                    widget = widget[PdfAttributes.Parent]
                key = self._get_widget_name(widget)
                if not key:
                    continue
                widget_type: Optional[str] = self._get_field_type(widget)
                if not widget_type:
                    continue

                value = widget[PdfAttributes.V] if PdfAttributes.V in widget else None
                if widget_type == "radio":
                    if value:
                        value = value[1:]
                    choices = []
                    if PdfAttributes.Kids in widget:
                        for each in widget[PdfAttributes.Kids]:
                            for each in each[PdfAttributes.AP][PdfAttributes.N].keys():
                                if each[1:] not in choices:
                                    choices.append(each[1:])

                elif widget_type == "checkbox":

                    if (
                        PdfAttributes.AP in widget
                        and PdfAttributes.N in widget[PdfAttributes.AP]
                        and PdfAttributes.D in widget[PdfAttributes.AP]
                        and PdfAttributes.AS in widget
                    ):
                        choices = [
                            each[1:] for each in (widget[PdfAttributes.AP][PdfAttributes.N]).keys()
                        ]
                        if "Off" not in choices:
                            choices.insert(0, "Off")
                elif widget_type in ["list", "combo"] and value:
                    choices = [each[1:] for each in widget[PdfAttributes.Opt]]
                if key not in loaded_widgets:
                    new_widget = self.TYPE_TO_OBJECT[widget_type](key, i, value)
                    if choices and isinstance(new_widget, CheckBoxWidget):
                        new_widget.choices = choices
                    elif isinstance(new_widget, TextWidget):
                        max_length = (
                            int(widget[PdfAttributes.MaxLen])
                            if PdfAttributes.MaxLen in widget
                            else None
                        )
                        if max_length:
                            new_widget.max_length = max_length
                    loaded_widgets[key] = new_widget
                else:
                    new_widget = loaded_widgets[key]
                    if choices and isinstance(new_widget, CheckBoxWidget):
                        for each in choices:
                            if new_widget.choices is not None:
                                if each not in new_widget.choices:
                                    new_widget.choices.append(each)
                            else:
                                new_widget.choices = [each]

                        cast(CheckBoxWidget, loaded_widgets[key]).choices = new_widget.choices

        self.widgets = loaded_widgets

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
        input_file: StrByteType,
        output_file: PathLike,
        data: Dict[str, Union[str, int, float, bool]],
        flatten: bool = True,
    ) -> "Pdf":
        """
        Fill the PDF form with data from a dictionary.

        Args:
            input_file (StrByteType): The template PDF, provided as either:
                - str: The file path to the PDF.
                - BinaryIO: An open file-like object containing the PDF data.
            output_file (PathLike): The output file path.
            data (Dict[str, Union[str, bool, int]]): A dictionary where keys are form field names
                and values are the data to fill the fields with.  Values can be strings, booleans,
                or integers.
            flatten (bool): Whether to flatten the form after filling, making the fields read-only
                (default: False).

        Returns:
            Pdf: The `Pdf` object, allowing for method chaining.
        """
        for key, value in data.items():
            if key in self.widgets:
                self.widgets[key].value = value

        reader = PdfReader(input_file)
        if self.adobe_mode:
            if (
                PdfAttributes.AcroForm in cast(Any, reader.trailer[PdfAttributes.Root])
                and PdfAttributes.XFA
                in cast(Any, reader.trailer[PdfAttributes.Root])[PdfAttributes.AcroForm]
            ):
                del cast(Any, reader.trailer[PdfAttributes.Root])[PdfAttributes.AcroForm][
                    PdfAttributes.XFA
                ]

        writer = PdfWriter(reader)
        if self.adobe_mode:
            writer.set_need_appearances_writer()

        fillers: Dict[str, Callable[[DictionaryObject, Any], None]] = {
            "checkbox": self._fill_checkbox,
            "text": self._fill_text,
            "radio": self._fill_radio,
        }

        output = PdfFillerOutput()
        for page in writer.pages:
            widgets: Optional[ArrayObject] = page.annotations
            if not widgets:
                continue
            for widget in widgets:
                if (
                    PdfAttributes.Subtype not in widget
                    or widget[PdfAttributes.Subtype] != PdfAttributes.Widget
                ):
                    continue

                annotation = cast(DictionaryObject, widget.get_object())
                if PdfAttributes.T not in widget:
                    widget = widget[PdfAttributes.Parent]
                widget_key: Optional[str] = self._get_widget_name(widget)
                if not widget_key or widget_key not in self.widgets:
                    continue

                widget_type: Optional[str] = self._get_field_type(widget)
                if not widget_type:
                    continue

                if widget_type != "radio":
                    self.flatten_generic(annotation, flatten)
                else:
                    self.flatten_radio(annotation, flatten)

                if widget_key not in data or widget_type not in fillers:
                    continue

                current_widget = self.widgets[widget_key]
                if current_widget.value is None:
                    continue

                output.debug(f"Filling {current_widget.name} with {current_widget.value}")
                fillers[widget_type](annotation, current_widget)

        with open(output_file, "wb") as f:
            writer.write(f)

        return self

    def _get_widget_name(self, widget: Any) -> Optional[str]:
        if PdfAttributes.T not in widget:
            return None
        key: Optional[str] = widget[PdfAttributes.T]
        if (
            PdfAttributes.Parent in widget
            and PdfAttributes.T in widget[PdfAttributes.Parent].get_object()
            and widget[PdfAttributes.Parent].get_object()[PdfAttributes.T] != key
        ):
            key = f"{self._get_widget_name(widget[PdfAttributes.Parent].get_object())}.{key}"

        return key

    def _get_field_type(self, annotation: Any) -> Optional[str]:
        """
        Determine widget type given its annotations.
        """
        ft = annotation[PdfAttributes.FT] if PdfAttributes.FT in annotation else None
        ff = annotation[PdfAttributes.Ff] if PdfAttributes.Ff in annotation else None

        if ft == PdfAttributes.Tx:
            return "text"
        if ft == PdfAttributes.Ch:
            if ff and int(ff) & 1 << 17:  # test 18th bit
                return "combo"
            return "list"
        if ft == PdfAttributes.Btn:
            if ff and int(ff) & 1 << 15:  # test 16th bit
                return "radio"
            return "checkbox"

        return None

    @staticmethod
    def _fill_text(annotation: DictionaryObject, widget: TextWidget) -> None:
        """
        Updates the value of a text annotation, setting the text content.

        This function modifies the value (V) and appearance (AP) of the text
        annotation to reflect the new text content.

        Args:
            annotation (DictionaryObject): The text annotation dictionary.
            widget (TextWidget): The Text widget object containing the text value.
        """
        if PdfAttributes.Parent in annotation and PdfAttributes.T not in annotation:
            annotation[NameObject(PdfAttributes.Parent)] = TextStringObject(widget.value)
            annotation[NameObject(PdfAttributes.AP)] = TextStringObject(widget.value)
        else:
            annotation[NameObject(PdfAttributes.V)] = TextStringObject(widget.value)
            annotation[NameObject(PdfAttributes.AP)] = TextStringObject(widget.value)

    @staticmethod
    def _fill_checkbox(annotation: DictionaryObject, widget: CheckBoxWidget) -> None:
        value: Union[bool, str, None] = widget.value
        if value is None:
            value = False
        if not isinstance(value, bool):
            annotation[NameObject(PdfAttributes.AS)] = NameObject("/" + widget.value)
            annotation[NameObject(PdfAttributes.V)] = NameObject("/" + widget.value)
            return

        for each in cast(Any, annotation[PdfAttributes.AP])[PdfAttributes.N]:
            if (value and str(each) != PdfAttributes.Off) or (
                not value and str(each) == PdfAttributes.Off
            ):
                annotation[NameObject(PdfAttributes.AS)] = NameObject(each)
                annotation[NameObject(PdfAttributes.V)] = NameObject(each)
                return

        if PdfAttributes.V in annotation:
            del annotation[PdfAttributes.V]
        if PdfAttributes.AS in annotation:
            del annotation[PdfAttributes.AS]

    @staticmethod
    def _fill_radio(annotation: DictionaryObject, widget: RadioWidget) -> None:

        for each in (
            cast(Any, annotation[PdfAttributes.Kids])
            if PdfAttributes.T in annotation
            else cast(Any, annotation[PdfAttributes.Parent])[PdfAttributes.Kids]
        ):
            # determine the export value of each kid
            keys = each[PdfAttributes.AP][PdfAttributes.N].keys()
            if PdfAttributes.Off in keys:
                keys.remove(PdfAttributes.Off)
            export = list(keys)[0] or None

            if f"/{widget.value}" == export:
                annotation[NameObject(PdfAttributes.AS)] = NameObject(export)
                cast(Any, annotation[NameObject(PdfAttributes.Parent)])[
                    NameObject(PdfAttributes.V)
                ] = NameObject(export)
            else:
                annotation[NameObject(PdfAttributes.AS)] = NameObject(PdfAttributes.Off)

    @staticmethod
    def flatten_radio(annot: DictionaryObject, val: bool) -> None:
        """
        Flattens a radio button annotation by setting or unsetting the ReadOnly flag,
        making it non-editable or editable based on the `val` parameter.

        This function modifies the Ff (flags) entry in the radio button's annotation
        dictionary or its parent dictionary if `Parent` exists in `annot`, to set or
        unset the ReadOnly flag, preventing or allowing the user from changing the
        selected option.

        Args:
            annot (DictionaryObject): The radio button annotation dictionary.
            val (bool): True to flatten (make read-only), False to unflatten (make editable).
        """
        if PdfAttributes.Parent in annot:
            cast(Any, annot[NameObject(PdfAttributes.Parent)])[NameObject(PdfAttributes.Ff)] = (
                NumberObject(
                    (
                        int(
                            cast(Any, annot[NameObject(PdfAttributes.Parent)]).get(
                                NameObject(PdfAttributes.Ff), 0
                            )
                        )
                        | PdfAttributes.READ_ONLY
                        if val
                        else int(
                            cast(Any, annot[NameObject(PdfAttributes.Parent)]).get(
                                NameObject(PdfAttributes.Ff), 0
                            )
                        )
                        & ~PdfAttributes.READ_ONLY
                    )
                )
            )
        else:
            annot[NameObject(PdfAttributes.Ff)] = NumberObject(
                (
                    int(annot.get(NameObject(PdfAttributes.Ff), 0)) | PdfAttributes.READ_ONLY
                    if val
                    else int(annot.get(NameObject(PdfAttributes.Ff), 0)) & ~PdfAttributes.READ_ONLY
                )
            )

    @staticmethod
    def flatten_generic(annot: DictionaryObject, val: bool) -> None:
        """
        Flattens a generic annotation by setting or unsetting the ReadOnly flag,
        making it non-editable or editable based on the `val` parameter.

        This function modifies the Ff (flags) entry in the annotation dictionary to
        set or unset the ReadOnly flag, preventing or allowing the user from
        interacting with the form field.

        Args:
            annot (DictionaryObject): The annotation dictionary.
            val (bool): True to flatten (make read-only), False to unflatten (make editable).
        """
        if PdfAttributes.Parent in annot and PdfAttributes.Ff not in annot:
            cast(Any, annot[NameObject(PdfAttributes.Parent)])[NameObject(PdfAttributes.Ff)] = (
                NumberObject(
                    (
                        int(annot.get(NameObject(PdfAttributes.Ff), 0)) | PdfAttributes.READ_ONLY
                        if val
                        else int(annot.get(NameObject(PdfAttributes.Ff), 0))
                        & ~PdfAttributes.READ_ONLY
                    )
                )
            )
        else:
            annot[NameObject(PdfAttributes.Ff)] = NumberObject(
                (
                    int(annot.get(NameObject(PdfAttributes.Ff), 0)) | PdfAttributes.READ_ONLY
                    if val
                    else int(annot.get(NameObject(PdfAttributes.Ff), 0)) & ~PdfAttributes.READ_ONLY
                )
            )
