import json
import os
import sys

import yaml

from pdffiller.cli.args import add_global_arguments
from pdffiller.cli.boolean_action import BooleanAction
from pdffiller.cli.command import pdffiller_command, PdfFillerArgumentParser
from pdffiller.cli.once_argument import OnceArgument
from pdffiller.exceptions import (
    AbortExecution,
    CommandLineError,
    FileNotExistsError,
    PdfFillerException,
)
from pdffiller.io.output import PdfFillerOutput
from pdffiller.pdf import Pdf
from pdffiller.typing import Any, Dict
from pdffiller.utils import normalize_field_data

from ..exit_codes import ERROR_ENCOUNTERED


@pdffiller_command(
    group=None,
)
def fill_form(parser: PdfFillerArgumentParser, *args: Any) -> Any:
    """
    Fill an input PDF's form fields with the data from
    """
    options_group = parser.add_argument_group("options")

    options_group.add_argument(
        "-d",
        "--data",
        metavar="DATA_PATH",
        type=str,
        help="""Path to the data file defining the field/value pairs.
                It can be a json or yaml file format.
                It can be also - to read data file from stdin with JSON format.
             """,
        action=OnceArgument,
    )

    options_group.add_argument(
        "-i",
        "--input-data",
        metavar="DATA",
        type=str,
        help="""Input data with JSON format defining the field/value pairs.
             """,
        action=OnceArgument,
    )

    options_group.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT_PATH",
        type=str,
        help="""Path to the output PDF file.""",
        action=OnceArgument,
    )

    options_group.add_argument(
        "-f",
        "--flatten",
        action=BooleanAction,
        default=False,
        help="Use this option to merge an input PDF's interactive form fields"
        "(and their data) with the PDF's pages. Defaults to False.",
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

    if not opts.data and not opts.input_data:
        raise CommandLineError("no data file path given")

    raw_data: Any = None
    if opts.input_data:
        try:
            raw_data = json.loads(opts.input_data)
        except Exception as exg:  # pylint: disable=broad-except
            output.error("Failed to load json input data")
            raise AbortExecution(ERROR_ENCOUNTERED) from exg
    else:
        if "-" != opts.data:
            if not os.path.isfile(opts.file):
                raise FileNotExistsError(opts.file)
            if not os.path.isfile(opts.data):
                raise FileNotExistsError(opts.data)

            with open(opts.data, "r", encoding="utf-8") as stream:
                try:
                    if os.path.splitext(opts.data)[1] in [".yaml", ".yml"]:
                        raw_data = yaml.safe_load(stream)
                    else:
                        raw_data = json.load(stream)
                except Exception as exg:  # pylint: disable=broad-except
                    output.error(f"Failed to load {opts.data} input data file")
                    raise AbortExecution(ERROR_ENCOUNTERED) from exg
        elif not os.isatty(sys.stdin.fileno()):
            try:
                raw_data = json.load(sys.stdin)
            except Exception as exg:  # pylint: disable=broad-except
                output.error(f"Failed to load {opts.data} input data file : " + str(exg))
                raise AbortExecution(ERROR_ENCOUNTERED) from exg

    input_data: Dict[str, str] = {}
    try:
        input_data.update(normalize_field_data(raw_data))
    except PdfFillerException as exp:
        output.error(str(exp))
        raise AbortExecution(ERROR_ENCOUNTERED) from exp

    if not input_data:
        output.warning("input data holds no field value to fill in")

    output.info(f"input file: {opts.file}")
    output.info("input values are:")
    output.info(json.dumps(input_data, indent=4))
    try:
        pdf = Pdf()
        pdf.fill(opts.file, opts.output, input_data, opts.flatten)
    except PdfFillerException as exp:
        output.error(str(exp))
    except Exception as exg:  # pylint: disable=broad-except # pragma: no cover
        output.error(f"unexpected error when adding {opts.file} with the following error:")
        output.error(exg)
        raise AbortExecution(ERROR_ENCOUNTERED) from exg
