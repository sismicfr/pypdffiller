import json

from pdffiller.io.output import cli_out_write
from pdffiller.typing import Any


def default_json_formatter(data: Any) -> None:
    """Default JSON formatter"""
    data_json = json.dumps(data, indent=4)
    cli_out_write(data_json)


def default_text_formatter(data: Any) -> None:
    """Default TEXT formatter"""
    for key, value in data.items():
        cli_out_write(f"{key}: {value}")
