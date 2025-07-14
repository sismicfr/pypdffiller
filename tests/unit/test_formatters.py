import pytest

from pdffiller import exceptions
from pdffiller.cli import formatters


def test_default_json(capsys):
    """test default json formatter"""
    formatters.default_json_formatter({})
    assert (
        capsys.readouterr().out
        == """{}
"""
    )

    formatters.default_json_formatter({"key": "value", "second": "val"})
    assert (
        capsys.readouterr().out
        == """{
    "key": "value",
    "second": "val"
}
"""
    )


def test_default_text(capsys):
    """test default text formatter"""
    formatters.default_text_formatter({})
    assert capsys.readouterr().out == """"""

    formatters.default_text_formatter({"key": "value", "second": "val"})
    assert (
        capsys.readouterr().out
        == """key: value
second: val
"""
    )
