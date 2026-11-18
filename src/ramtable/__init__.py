"""Public RAMTable API.

Expose ``Columns``, ``Rows``, ``Table``, and ``TypeValidator`` from the
``ramtable`` package as a concise, stable import path, along with the
installed package version.
"""

from importlib.metadata import PackageNotFoundError, version

from .columns import Columns
from .rows import Rows
from .table import Table
from .types import TypeValidator

try:
    __version__ = version("ramtable")
except PackageNotFoundError:  # pragma: no cover - not installed
    __version__ = "0+unknown"

__all__ = [
    "Columns",
    "Rows",
    "Table",
    "TypeValidator",
    "__version__",
]
