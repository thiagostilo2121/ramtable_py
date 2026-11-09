"""API pública de RAMTable.

Expone :class:`Columns`, :class:`Rows` y :class:`Table` desde el paquete
``ramtable`` para ofrecer una ruta de importación concisa y estable.
"""

from .columns import Columns
from .rows import Rows
from .table import Table

__all__ = [
    "Columns",
    "Rows",
    "Table",
]
