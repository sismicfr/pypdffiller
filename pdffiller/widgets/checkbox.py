"""
Module representing a checkbox widget.

This module defines the Checkbox class, which is a subclass of the
Widget class. It represents a checkbox form field in a PDF document.
"""

from typing import Any, Dict, List, Optional

from .base import Widget


class CheckBoxWidget(Widget):
    """
    Represents a checkbox widget.

    The Checkbox class provides a concrete implementation for
    checkbox form fields. It inherits from the Widget class and
    implements the schema_definition and sample_value properties.
    """

    def __init__(
        self,
        name: str,
        page_number: int,
        value: Optional[str] = None,
        readonly: bool = False,
        choices: Optional[List[str]] = None,
    ) -> None:
        """
        Initializes a checkbox widget.

        Args:
            name (str): The name of the checkbox.
            page_number (int): The associated page index
            value (str): The initial value of the checkbox. Defaults to None.
            readonly (bool): True if readonly is set, else False.
            choices: The list of available choices. Defaults to None.
        """
        super().__init__(name, page_number, value, readonly)
        self.choices: Optional[List[str]] = choices

    @property
    def schema_definition(self) -> Dict[str, Any]:
        """
        Returns the schema definition for the checkbox.

        The schema definition is a dictionary that describes the
        data type and other constraints for the checkbox value.

        Returns:
            dict: A dictionary representing the schema definition.
        """
        return {"FieldType": "checkbox", "FieldOptions": self.choices, **super().schema_definition}
