import json
import os

from pdffiller.cli.args import add_global_arguments
from pdffiller.cli.command import pdffiller_command, PdfFillerArgumentParser
from pdffiller.exceptions import (
    AbortExecution,
    CommandLineError,
    FileNotExistsError,
    PdfFillerException,
)
from pdffiller.io.output import cli_out_write, PdfFillerOutput
from pdffiller.pdf import Pdf
from pdffiller.typing import Any

from ..exit_codes import ERROR_ENCOUNTERED


def dump_fields_text_formatter(pdf: Pdf) -> None:
    """Print output text for dump_fields command as simple text"""
    for widget in pdf.schema:
        cli_out_write("----------")
        for key, value in widget.items():
            if isinstance(value, list):
                for subvalue in value:
                    cli_out_write(f"{key}: {subvalue}")
            else:
                cli_out_write(f"{key}: {value}")


def dump_fields_json_formatter(pdf: Pdf) -> None:
    """Print output text for dump_fields command as simple text"""

    cli_out_write(json.dumps(pdf.schema, indent=4, ensure_ascii=False))


@pdffiller_command(
    group=None,  # "Extract",
    formatters={"text": dump_fields_text_formatter, "json": dump_fields_json_formatter},
)
def dump_data_fields(parser: PdfFillerArgumentParser, *args: Any) -> Any:
    """
    Dump form fields present in a pdf given its file path
    """
    options_group = parser.add_argument_group("options")
    parser.add_argument(
        "file",
        metavar="INPUT_PATH",
        type=str,
        nargs="?",
        help="""Path to the input PDF file.""",
    )

    add_global_arguments(options_group, True, parser)

    opts = parser.parse_args(*args)

    output = PdfFillerOutput()
    if not opts.file:
        raise CommandLineError("no input file given")

    if not os.path.isfile(opts.file):
        raise FileNotExistsError(opts.file)

    try:
        pdf = Pdf(opts.file)
        return pdf
    except PdfFillerException as exp:
        output.error(str(exp))
    except Exception as exg:  # pylint: disable=broad-except # pragma: no cover
        output.error(f"unexpected error when adding {opts.file} with the following error:")
        output.error(exg)
        raise AbortExecution(ERROR_ENCOUNTERED) from exg

    return None
