"""
Module representing a radio button widget.

This module defines the Radio class, which is a subclass of the
Checkbox class. It represents a radio button form field in a PDF
document, allowing users to select one option from a group of choices.
"""

from typing import Any, Dict

from .checkbox import CheckBoxWidget


class RadioWidget(CheckBoxWidget):
    """
    Represents a radio button widget.

    The Radio class provides a concrete implementation for radio button
    form fields. It inherits from the Checkbox class and implements
    the schema_definition and sample_value properties.
    """

    @property
    def schema_definition(self) -> Dict[str, Any]:
        """
        Returns the schema definition for the checkbox.

        The schema definition is a dictionary that describes the
        data type and other constraints for the checkbox value.

        Returns:
            dict: A dictionary representing the schema definition.
        """
        return {
            **super().schema_definition,
            "FieldType": "radio",
        }
