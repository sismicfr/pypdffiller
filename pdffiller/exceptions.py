from pdffiller.typing import Optional, PathLike


#
# Generic exception
#
class PdfFillerException(Exception):
    """PdfFiller based exception object"""

    def __init__(self, message: str) -> None:
        Exception.__init__(self, message)
        self.message = message


#
# Command-line utility exception
#


class AbortExecution(PdfFillerException):
    """Abort but with success the current execution"""

    def __init__(self, exitcode: int = 0) -> None:
        self.exitcode = exitcode
        PdfFillerException.__init__(self, "")


class CommandLineError(PdfFillerException):
    """One command-line argument is not defined properly"""

    def __init__(self, message: str) -> None:
        PdfFillerException.__init__(self, message)


class InvalidCommandNameException(PdfFillerException):
    """Invalid command or action name"""

    def __init__(self, name: Optional[str] = None) -> None:
        if name:
            PdfFillerException.__init__(self, f"Unknown '{name}' command")
        else:
            PdfFillerException.__init__(self, "No command name given")


class InvalidSubCommandNameException(PdfFillerException):
    """Invalid sub-command name"""

    def __init__(self, name: Optional[str] = None) -> None:
        if name:
            PdfFillerException.__init__(self, f"Unknown '{name}' sub-command")
        else:
            PdfFillerException.__init__(self, "No sub-command name given")


class FileNotExistsError(PdfFillerException):
    """File not found"""

    def __init__(self, pathname: PathLike) -> None:
        PdfFillerException.__init__(self, f"{pathname} : file not found")
