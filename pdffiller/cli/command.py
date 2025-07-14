import argparse

from pdffiller.cli.once_argument import OnceArgument
from pdffiller.cli.smart_formatter import SmartFormatter
from pdffiller.exceptions import (
    AbortExecution,
    InvalidSubCommandNameException,
    PdfFillerException,
)
from pdffiller.io.output import PdfFillerOutput
from pdffiller.typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    SubParserType,
    Union,
)


class PdfFillerArgumentParser(argparse.ArgumentParser):
    """PdfFiller argument parser to support configuration file"""

    _command: "PdfFillerCommand"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def parse_args(  # type: ignore[override] # pylint: disable=arguments-differ
        self, args: Optional[Sequence[str]] = None
    ) -> argparse.Namespace:
        options = super().parse_args(args)

        PdfFillerOutput.define_log_level(options.verbosity)
        PdfFillerOutput.define_log_output(options.log_file)
        output = PdfFillerOutput()

        if "help" in options and options.help:
            self.print_help(output.stream)
            raise AbortExecution(0)

        return options


CommandCallback = Callable[[PdfFillerArgumentParser, Any], Any]
"""Command callback function.
:param PdfFillerArgumentParser: Current parser object
:param Any: Command-line arguments as a list
:return: Depend on each command.
"""

SubCommandCallback = Callable[[PdfFillerArgumentParser, argparse.ArgumentParser, Any], Any]
"""Sub-command callback function.
:param PdfFillerArgumentParser: Current parser object
:param argparse.ArgumentParser: The command sub-parser object
:param Any: Command-line arguments as a list
:return: Depend on each command.
"""

FormatterCallback = Callable[[Any], None]
"""Formatter callback function.
    :param Dict: Output format keyword with its callback function function
"""


class BaseCommand:
    """Base PdfFiller command"""

    def __init__(
        self,
        name: str,
        callback: Union[CommandCallback, SubCommandCallback],
        formatters: Optional[Dict[str, FormatterCallback]] = None,
    ) -> None:
        self.formatters: Dict[str, FormatterCallback] = {"text": lambda x: None}
        self.callback = callback
        self.callback_name: str = name
        if formatters:
            for kind, action in formatters.items():
                if callable(action):
                    self.formatters[kind] = action
                else:
                    raise PdfFillerException(
                        f"Invalid formatter for {kind}. The formatter must be" "a valid function"
                    )
        if callback.__doc__:
            self.callback_doc = callback.__doc__
        else:
            raise PdfFillerException(
                f"No documentation string defined for command: '{self.callback_name}'."
                " PdfFiller commands should provide a documentation string explaining "
                "its use briefly."
            )

    @staticmethod
    def init_log_levels(parser: argparse.ArgumentParser) -> None:
        """Add verbosity command-line option"""
        parser.add_argument(
            "-V",
            "--verbosity",
            default="status",
            metavar="LEVEL",
            nargs="?",
            type=str,
            help="Level of detail of the output. Valid options from less verbose "
            "to more verbose: -Vquiet, -Verror, -Vwarning, -Vnotice, -Vstatus, "
            "-V or -Vverbose, -VV or -Vdebug, -VVV or -vtrace",
        )

    @staticmethod
    def init_log_file(parser: argparse.ArgumentParser) -> None:
        """Add output log file command-line option"""
        parser.add_argument(
            "-L",
            "--log-file",
            metavar="PATH",
            type=str,
            help="Send output to PATH instead of stderr.",
            action=OnceArgument,
        )

    @property
    def _help_formatters(self) -> List[str]:
        """
        Formatters that are shown as available in help, 'text' formatter
        should not appear
        """
        return [formatter for formatter in self.formatters if formatter != "text"]

    def init_formatters(self, parser: argparse.ArgumentParser) -> None:
        """Add formatters command-line options."""
        formatters = self._help_formatters
        if formatters:
            parser.add_argument(
                "-f",
                "--format",
                metavar="NAME",
                action=OnceArgument,
                help=f"Select the output format: {', '.join(formatters)}",
            )

    @property
    def name(self) -> str:
        """Get action name"""
        return self.callback_name

    @property
    def method(self) -> Union[CommandCallback, SubCommandCallback]:
        """Get action method"""
        return self.callback

    @property
    def doc(self) -> str:
        """Get action help message"""
        return self.callback_doc

    def _format(self, parser: argparse.ArgumentParser, info: Dict[str, Any], *args: Any) -> None:
        parser_args, _ = parser.parse_known_args(*args)

        default_format = "text"
        try:
            formatarg = parser_args.format or default_format
        except AttributeError:
            formatarg = default_format

        try:
            formatter = self.formatters[formatarg]
        except KeyError as exc:
            raise PdfFillerException(
                f"{formatarg} is not a known format. Supported formatters are: "
                f"{', '.join(self._help_formatters)}"
            ) from exc

        formatter(info)


class PdfFillerCommand(BaseCommand):
    """Main PdfFiller command object"""

    def __init__(
        self,
        cb: CommandCallback,
        group: Optional[str] = None,
        formatters: Optional[Dict[str, FormatterCallback]] = None,
        callback_name: Optional[str] = None,
    ) -> None:
        if not callback_name:
            callback_name = cb.__name__.replace("_", "-")
        super().__init__(callback_name, cb, formatters=formatters)
        self.subcommands: Dict[str, "PdfFillerSubCommand"] = {}
        self.group_name = group  # or "Other"

    def add_subcommand(self, subcommand: "PdfFillerSubCommand") -> None:
        """Register new sub-command"""
        subcommand.set_name(self.callback_name)
        self.subcommands[subcommand.callback_name] = subcommand

    def _docs(self) -> PdfFillerArgumentParser:
        parser = PdfFillerArgumentParser(
            description=self.callback_doc,
            prog=f"pdffiller {self.callback_name}",
            formatter_class=SmartFormatter,
            add_help=False,
        )
        return parser

    def run(self, *args: Any) -> None:
        """Parse and execute requested command"""
        parser = PdfFillerArgumentParser(
            description=self.callback_doc,
            prog=f"pdffiller {self.callback_name}",
            formatter_class=SmartFormatter,
            add_help=False,
        )
        # pylint: disable=protected-access
        parser._command = self
        info = self.callback(parser, *args)

        if not self.subcommands:
            self._format(parser, info, *args)
        else:
            subcommand_parser: SubParserType = parser.add_subparsers(
                dest="subcommand",
            )
            subcommand_parser.required = True
            try:
                sub = self.subcommands[args[0][0]]
            except (KeyError, IndexError):  # display help
                for sub in self.subcommands.values():
                    sub.set_parser(subcommand_parser)
                parser.print_help()
                raise InvalidSubCommandNameException(  # pylint: disable=raise-missing-from
                    args[0][0] if len(args[0]) else ""
                )

            sub.set_parser(subcommand_parser)
            sub.run(parser, *args)

    @property
    def group(self) -> Optional[str]:
        """Gets group name."""
        return self.group_name


class PdfFillerSubCommand(BaseCommand):
    """PdfFiller sub-command"""

    parser: argparse.ArgumentParser

    def __init__(
        self,
        cb: SubCommandCallback,
        formatters: Optional[Dict[str, FormatterCallback]] = None,
    ) -> None:
        super().__init__("", cb, formatters=formatters)
        self.subcommand_name = cb.__name__.replace("_", "-")

    def run(self, parent_parser: PdfFillerArgumentParser, *args: object) -> None:
        """Execute the sub-command"""
        setattr(self.parser, "_command", self)
        info = self.callback(parent_parser, self.parser, *args)
        self._format(parent_parser, info, *args)

    def set_name(self, parent_name: str) -> None:
        """Set sub-command name"""
        self.callback_name = self.subcommand_name.replace(f"{parent_name}-", "", 1)

    def set_parser(self, subcommand_parser: SubParserType) -> None:
        """Set the associated parser"""
        self.parser = subcommand_parser.add_parser(
            self.callback_name, help=self.callback_doc, add_help=True
        )
        self.parser.description = self.callback_doc


def pdffiller_command(
    group: Optional[str],
    formatters: Optional[Dict[str, FormatterCallback]] = None,
    name: Optional[str] = None,
) -> Callable[[CommandCallback], PdfFillerCommand]:
    """Register a PdfFiller command"""
    return lambda f: PdfFillerCommand(f, group, formatters=formatters, callback_name=name)


def pdffiller_subcommand(
    formatters: Optional[Dict[str, FormatterCallback]] = None
) -> Callable[[SubCommandCallback], PdfFillerSubCommand]:
    """Register a PdfFiller sub-command"""
    return lambda f: PdfFillerSubCommand(f, formatters=formatters)
