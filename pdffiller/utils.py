import html
import os
from pathlib import Path

from pdffiller.exceptions import PdfFillerException
from pdffiller.typing import Any, Dict, Optional, PathLike, Sequence

#: Accepted key names holding the field name in a list based input data
FIELD_NAME_KEYS = ("name", "FieldName", "field_name")

#: Accepted key names holding the field value in a list based input data
FIELD_VALUE_KEYS = ("value", "FieldValue", "field_value")

_MISSING = object()


def str_to_path(path: Optional[PathLike]) -> Any:
    """Convert string or Path to Path

    :param path: The path to be converted
    :return: The converted path into Path object if successful, else None
    """
    if not path:
        return None

    if not isinstance(path, Path):
        try:
            new_path = Path(str(path))
        except RuntimeError:
            new_path = None
    else:
        new_path = path

    return new_path


def path_to_str(path: Optional[PathLike]) -> Any:
    """Convert string or path to string only

    :param path: The path to be converted
    :return: The converted string from ``path`` if successful, else None
    """
    if not path:
        return None

    return os.fspath(path)


def _lookup(entry: Dict[Any, Any], keys: Sequence[str]) -> Any:
    """Return the value of the first key of ``keys`` found in ``entry``

    :param entry: The mapping to look into
    :param keys: The candidate key names, by order of precedence
    :return: The value found, else the ``_MISSING`` sentinel
    """
    for key in keys:
        if key in entry:
            return entry[key]

    return _MISSING


def to_field_value(value: Any, name: Optional[str] = None) -> str:
    """Convert a value coming from a json/yaml input data into a pdf field value

    ``None`` is converted to an empty string, thus clearing the field, and booleans
    are converted to the ``On``/``Off`` pdf states so that checkboxes can be driven
    with ``true``/``false``.

    :param value: The value to be converted
    :param name: The field name the value belongs to, used for error reporting only
    :return: The value as a string
    :raises PdfFillerException: when the value cannot be used as a field value
    """
    if value is None:
        return ""

    if isinstance(value, bool):
        return "On" if value else "Off"

    if isinstance(value, str):
        return value

    if isinstance(value, (int, float)):
        return str(value)

    location = f" for field '{name}'" if name else ""
    raise PdfFillerException(
        f"unsupported {type(value).__name__} value{location}: "
        "expecting a string, a number, a boolean or null"
    )


def normalize_field_data(data: Any) -> Dict[str, str]:
    """Normalize input data into a field name to field value mapping

    Both supported input data layouts are accepted:

    * a mapping, i.e. ``{"Lastname": "Doe"}``
    * a list of entries, i.e. ``[{"name": "Lastname", "value": "Doe"}]``, where the
      keys may also be spelled ``FieldName``/``FieldValue`` as dumped by the
      ``dump_data_fields`` command. Names and values of such entries are html
      unescaped, as they usually come from a serialized html form. An entry without
      any value key clears the field.

    :param data: The raw data as loaded from the json/yaml input
    :return: The field name to field value mapping
    :raises PdfFillerException: when the input data layout is not supported
    """
    if data is None:
        return {}

    if isinstance(data, dict):
        return {str(name): to_field_value(value, str(name)) for name, value in data.items()}

    if isinstance(data, list):
        fields: Dict[str, str] = {}
        for index, entry in enumerate(data):
            if not isinstance(entry, dict):
                raise PdfFillerException(
                    f"invalid input data: entry #{index + 1} is a {type(entry).__name__} "
                    "while expecting an object holding a "
                    f"{' or '.join(repr(key) for key in FIELD_NAME_KEYS)} key"
                )

            name = _lookup(entry, FIELD_NAME_KEYS)
            if name is _MISSING:
                raise PdfFillerException(
                    f"invalid input data: entry #{index + 1} has no "
                    f"{' or '.join(repr(key) for key in FIELD_NAME_KEYS)} key"
                )

            value = _lookup(entry, FIELD_VALUE_KEYS)
            name = html.unescape(str(name))
            if isinstance(value, str):
                value = html.unescape(value)
            elif value is _MISSING:
                value = None

            fields[name] = to_field_value(value, name)

        return fields

    raise PdfFillerException(
        f"invalid input data: expecting an object or a list of objects, "
        f"got a {type(data).__name__}"
    )
