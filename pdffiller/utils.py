import os
from pathlib import Path

from pdffiller.typing import Any, Optional, PathLike


def str_to_path(path: Optional[PathLike]) -> Any:
    """Convert string or Path to Path

    :param path: The path to be converted
    :return: The converted path into Path object if successful, else None
    """
    if not path:
        return None

    if not isinstance(path, Path):
        try:
            new_path = Path(str(path))
        except RuntimeError:
            new_path = None
    else:
        new_path = path

    return new_path


def path_to_str(path: Optional[PathLike]) -> Any:
    """Convert string or path to string only

    :param path: The path to be converted
    :return: The converted string from ``path`` if successful, else None
    """
    if not path:
        return None

    return os.fspath(path)
