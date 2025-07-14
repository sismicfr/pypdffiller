import argparse
from pathlib import Path
from typing import (
    Any,
    Callable,
    cast,
    Dict,
    Generator,
    IO,
    ItemsView,
    List,
    Mapping,
    Optional,
    overload,
    Sequence,
    Tuple,
    Type,
    TYPE_CHECKING,
    TypedDict,
    TypeVar,
    Union,
)

__all__ = [
    "cast",
    "overload",
    "Any",
    "Callable",
    "Dict",
    "ExitCode",
    "Generator",
    "IO",
    "ItemsView",
    "List",
    "Optional",
    "Mapping",
    "PathLike",
    "Sequence",
    "Tuple",
    "TypedDict",
    "TypeVar",
    "Type",
    "Union",
    "SubParserType",
    "StrByteType",
]


ExitCode = Union[str, int, None]
PathLike = Union[str, Path]

StreamType = IO[Any]
StrByteType = Union[PathLike, StreamType]

if TYPE_CHECKING:
    # pylint: disable=protected-access,line-too-long
    SubParserType = argparse._SubParsersAction["PdfFillerStoreArgumentParser"]  # type: ignore[name-defined]
else:
    SubParserType = Any
