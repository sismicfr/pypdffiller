"""
Module representing a text field widget.

This module defines the Text class, which is a subclass of the
Widget class. It represents a text field form field in a PDF document,
allowing users to enter text.
"""

from typing import Any, Dict, Optional

from .base import Widget


class TextWidget(Widget):
    """
    Represents a text field widget.

    The Text class provides a concrete implementation for text field
    form fields. It inherits from the Widget class and implements
    the value, schema_definition.
    """

    def __init__(
        self,
        name: str,
        page_number: int,
        value: Optional[str] = None,
        readonly: bool = False,
        max_length: Optional[int] = None,
    ) -> None:
        """
        Initializes a text widget.

        Args:
            name (str): The name of the checkbox.
            page_number (int): The associated page index
            value (str): The initial value of the checkbox. Defaults to None.
            readonly (bool): True if readonly is set, else False.
            max_length (int): The maximum length of the text field. Defaults to None.
        """
        super().__init__(name, page_number, value, readonly)
        self.max_length: Optional[int] = max_length

    @property
    def value(self) -> str:
        """
        Returns the value of the text field.

        If the value is an integer or float, it is converted to a string.

        Returns:
            str: The value of the text field.
        """
        if isinstance(self._value, (int, float)):
            return str(self._value)

        return self._value or ""

    @value.setter
    def value(self, value: Optional[str]) -> None:
        """
        Sets the value of the text field.

        Args:
            value (str): The value to set.
        """
        self._value = value

    @property
    def schema_definition(self) -> Dict[str, Any]:
        """
        Returns the schema definition for the checkbox.

        The schema definition is a dictionary that describes the
        data type and other constraints for the checkbox value.

        Returns:
            dict: A dictionary representing the schema definition.
        """
        schema: Dict[str, Any] = {"FieldType": "text", **super().schema_definition}
        if self.max_length:
            schema["MaxLength"] = self.max_length

        return schema
