"""Public RAMTable API.

Expose :class:`Columns`, :class:`Rows`, and :class:`Table` from the
``ramtable`` package as a concise, stable import path, along with the
installed package version.
"""

from importlib.metadata import PackageNotFoundError, version

from .columns import Columns
from .rows import Rows
from .table import Table

try:
    __version__ = version("ramtable")
except PackageNotFoundError:  # pragma: no cover - source checkout without install
    __version__ = "0+unknown"

__all__ = [
    "__version__",
    "Columns",
    "Rows",
    "Table",
]
