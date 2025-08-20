"""
This module defines the base class for all widgets in PyPdfFormFiller.

This module defines the base class for form widgets, which are used to
represent form fields in a PDF document. The Widget class provides
common attributes and methods for all form widgets, such as name, value,
and schema definition.
"""

from typing import Any, Dict, Optional


class Widget:
    """
    Base class for form widget.

    The Widget class provides a base implementation for form widgets,
    which are used to represent form fields in a PDF document. It
    defines common attributes and methods for all form widgets, such
    as name, value, and schema definition.
    """

    def __init__(
        self, name: str, page_number: int, value: Optional[Any] = None, readonly: bool = False
    ) -> None:
        """
        Initialize a new widget.

        Args:
            name (str): The name of the widget.
            page_number (int): The associated page index
            value (Any): The initial value of the widget. Defaults to None.
            readonly (bool): True if readonly is set, else False.
        """
        super().__init__()
        self._name: str = name
        self.page_number: int = page_number
        self._value: Optional[Any] = value
        self._readonly: bool = readonly
        self._description: Optional[str] = None

    @property
    def name(self) -> str:
        """
        Get the name of the widget.

        Returns:
            str: The name of the widget.
        """
        return self._name

    @property
    def value(self) -> Any:
        """
        Get the value of the widget.

        Returns:
            Any: The value of the widget.
        """
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """
        Set the value of the widget.

        Args:
            value (Any): The value to set.
        """
        self._value = value

    @property
    def readonly(self) -> bool:
        """
        Determine whether readonly mode is set or not.

        Returns:
            bool: True if readonly mode is set, else False.
        """
        return self._readonly

    @readonly.setter
    def readonly(self, readonly: bool) -> None:
        """
        Specify if the readonly mode is set

        Args:
            readonly (bool): True if readonly mode is set, else False.
        """
        self._readonly = readonly

    @property
    def description(self) -> Optional[str]:
        """
        Get the description of the widget.

        Returns:
            Any: The description of the widget.
        """
        return self._description

    @description.setter
    def description(self, description: Optional[str]) -> None:
        """
        Set the description of the widget.

        Args:
            description (str): The description to set.
        """
        self._description = description

    @property
    def schema_definition(self) -> Dict[str, Any]:
        """
        Get the schema definition of the widget.

        This method returns a dictionary that defines the schema
        for the widget. The schema definition is used to validate
        the widget's value.

        Returns:
            dict: The schema definition of the widget.
        """
        result: Dict[str, Any] = {"FieldName": self._name}
        if self._value:
            result["FieldValue"] = self._value

        if self._readonly:
            result["Readonly"] = self._readonly

        if self._description is not None:
            result["Description"] = self._description

        return result
