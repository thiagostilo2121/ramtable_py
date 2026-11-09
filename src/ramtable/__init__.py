"""Public RAMTable API.

Expose :class:`Columns`, :class:`Rows`, and :class:`Table` from the
``ramtable`` package as a concise, stable import path.
"""

from .columns import Columns
from .rows import Rows
from .table import Table

__all__ = [
    "Columns",
    "Rows",
    "Table",
]
