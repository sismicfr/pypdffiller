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


def embed_font_text_formatter(changed: List[Dict[str, Any]]) -> None:
    """Print changed fields as plain text"""
    if not changed:
        cli_out_write("No fields were changed.")
        return
    for field in changed:
        cli_out_write("----------")
        for key, value in field.items():
            cli_out_write(f"{key}: {value}")


def embed_font_json_formatter(changed: List[Dict[str, Any]]) -> None:
    """Print changed fields as JSON"""
    if not changed:
        return
    cli_out_write(json.dumps(changed, indent=4, ensure_ascii=False))


@pdffiller_command(
    group=None,
    formatters={"text": embed_font_text_formatter, "json": embed_font_json_formatter},
)
def embed_font(parser: PdfFillerArgumentParser, *args: Any) -> Any:
    """
    Embed a TrueType font in a PDF form and make its text fields use it.
    fill_form then draws the values with that font.
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
        "--font",
        metavar="FONT_PATH",
        type=str,
        help="""Path to the TrueType font file (.ttf) to embed.""",
        action=OnceArgument,
    )

    options_group.add_argument(
        "--name",
        metavar="NAME",
        type=str,
        help="""Resource name of the font in the form.
                Default: the PostScript name of the font.""",
        action=OnceArgument,
    )

    options_group.add_argument(
        "--size",
        metavar="SIZE",
        type=float,
        help="""Font size of the fields, 0 for the automatic size.
                Default: keep the size of each field.""",
        action=OnceArgument,
    )

    options_group.add_argument(
        "--fields",
        metavar="NAMES",
        type=str,
        help="""Comma-separated names of the text fields to change.
                Default: all the text fields.""",
        action=OnceArgument,
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

    if not opts.font:
        raise CommandLineError("no font file given")

    for path in (opts.file, opts.font):
        if not os.path.isfile(path):
            raise FileNotExistsError(path)

    fields = (
        [name.strip() for name in opts.fields.split(",") if name.strip()] if opts.fields else None
    )

    try:
        pdf = Pdf()
        changed = pdf.embed_font(opts.file, opts.output, opts.font, opts.name, opts.size, fields)
        output.info(f"pdf with embedded font saved to {opts.output}")
        return changed
    except PdfFillerException as exp:
        output.error(str(exp))
        raise AbortExecution(ERROR_ENCOUNTERED) from exp
    except Exception as exg:  # pylint: disable=broad-except # pragma: no cover
        output.error(
            f"unexpected error when embedding a font in {opts.file} with the following error:"
        )
        output.error(exg)
        raise AbortExecution(ERROR_ENCOUNTERED) from exg
