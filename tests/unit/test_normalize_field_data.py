import pytest

from pdffiller.exceptions import PdfFillerException
from pdffiller.utils import normalize_field_data, to_field_value


def test_mapping_input():
    assert normalize_field_data({"Lastname": "Doe"}) == {"Lastname": "Doe"}


def test_no_input():
    assert normalize_field_data(None) == {}


def test_list_input():
    data = [
        {"name": "Lastname", "value": "Doe"},
        {"name": "Firstname", "value": "John"},
    ]
    assert normalize_field_data(data) == {"Lastname": "Doe", "Firstname": "John"}


def test_empty_list_input():
    """an empty list is a valid input holding no field to fill in"""
    assert normalize_field_data([]) == {}


def test_list_input_with_dumped_keys():
    """the keys dumped by the dump_data_fields command are accepted as well"""
    data = [
        {"FieldName": "Lastname", "FieldValue": "Doe"},
        {"field_name": "Firstname", "field_value": "John"},
    ]
    assert normalize_field_data(data) == {"Lastname": "Doe", "Firstname": "John"}


def test_list_input_without_value():
    """an entry without any value key clears the field"""
    assert normalize_field_data([{"FieldName": "Lastname"}]) == {"Lastname": ""}


def test_list_input_is_unescaped():
    data = [{"name": "Last&amp;name", "value": "Doe &gt; Do"}]
    assert normalize_field_data(data) == {"Last&name": "Doe > Do"}


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Doe", "Doe"),
        (None, ""),
        (True, "On"),
        (False, "Off"),
        (42, "42"),
        (4.5, "4.5"),
    ],
)
def test_value_conversion(value, expected):
    assert to_field_value(value) == expected
    assert normalize_field_data({"Lastname": value}) == {"Lastname": expected}
    assert normalize_field_data([{"name": "Lastname", "value": value}]) == {"Lastname": expected}


@pytest.mark.parametrize("data", [42, "Doe", ["Lastname"], [42], [["Lastname", "Doe"]]])
def test_invalid_input_layout(data):
    with pytest.raises(PdfFillerException):
        normalize_field_data(data)


def test_list_input_without_name():
    with pytest.raises(PdfFillerException):
        normalize_field_data([{"Readonly": True}])


@pytest.mark.parametrize("value", [["Doe"], {"last": "Doe"}])
def test_unsupported_value(value):
    with pytest.raises(PdfFillerException):
        normalize_field_data({"Lastname": value})
