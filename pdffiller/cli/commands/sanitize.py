import json
import os

from pdffiller.cli.args import add_global_arguments
from pdffiller.cli.command import pdffiller_command, PdfFillerArgumentParser
from pdffiller.cli.once_argument import OnceArgument
from pdffiller.exceptions import (
    AbortExecution,
    CommandLineError,
    FileNotExistsError,
    PdfFillerException,
)
from pdffiller.io.output import cli_out_write, PdfFillerOutput
from pdffiller.pdf import Pdf
from pdffiller.typing import Any, Dict, List

from ..exit_codes import ERROR_ENCOUNTERED


def sanitize_text_formatter(sanitized: List[Dict[str, Any]]) -> None:
    """Print sanitized fields as plain text"""
    if not sanitized:
        cli_out_write("No fields were sanitized.")
        return
    for field in sanitized:
        cli_out_write("----------")
        for key, value in field.items():
            cli_out_write(f"{key}: {value}")


def sanitize_json_formatter(sanitized: List[Dict[str, Any]]) -> None:
    """Print sanitized fields as JSON"""
    if not sanitized:
        return
    cli_out_write(json.dumps(sanitized, indent=4, ensure_ascii=False))


@pdffiller_command(
    group=None,
    formatters={"text": sanitize_text_formatter, "json": sanitize_json_formatter},
)
def sanitize(parser: PdfFillerArgumentParser, *args: Any) -> Any:
    """
    Sanitize a PDF by removing MaxLen constraints from text fields.
    This fixes PDFs where MaxLen is incorrectly set, causing text truncation.
    """
    options_group = parser.add_argument_group("options")

    options_group.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT_PATH",
        type=str,
        help="""Path to the output PDF file.""",
        action=OnceArgument,
    )

    options_group.add_argument(
        "--deep",
        action="store_true",
        default=False,
        help="Perform a deep sanitization: also clear the Comb flag from text fields.",
    )

    parser.add_argument(
        "file",
        metavar="INPUT_PATH",
        type=str,
        nargs="?",
        help="""Path to the input PDF file.""",
        action=OnceArgument,
    )

    add_global_arguments(options_group, True, parser)

    opts = parser.parse_args(*args)

    output = PdfFillerOutput()
    if not opts.file:
        raise CommandLineError("no input file given")

    if not opts.output:
        raise CommandLineError("no output file path given")

    if not os.path.isfile(opts.file):
        raise FileNotExistsError(opts.file)

    try:
        pdf = Pdf()
        sanitized = pdf.sanitize(opts.file, opts.output, opts.deep)
        output.info(f"sanitized pdf saved to {opts.output}")
        return sanitized
    except PdfFillerException as exp:
        output.error(str(exp))
    except Exception as exg:  # pylint: disable=broad-except # pragma: no cover
        output.error(f"unexpected error when sanitizing {opts.file} with the following error:")
        output.error(exg)
        raise AbortExecution(ERROR_ENCOUNTERED) from exg

    return None
