import argparse

from pdffiller.cli.command import BaseCommand
from pdffiller.typing import Any, Optional, Union


def add_global_arguments(
    parser: Union[argparse.ArgumentParser, Any],
    add_help: bool = True,
    main_parser: Optional[argparse.ArgumentParser] = None,
) -> None:
    """Add global parsers command-line options."""
    BaseCommand.init_log_file(parser)
    BaseCommand.init_log_levels(parser)

    if hasattr(parser, "_command"):
        getattr(parser, "_command").init_formatters(parser)
    elif main_parser and hasattr(main_parser, "_command"):
        getattr(main_parser, "_command").init_formatters(parser)
    if add_help:
        parser.add_argument(
            "-h",
            "--help",
            dest="help",
            action="store_true",
            default=False,
            help="show this help message and exit",
        )
