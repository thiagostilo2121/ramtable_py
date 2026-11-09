
"""Contenedor principal que coordina el esquema y las filas."""

from typing import Any

from .columns import Columns
from .rows import Rows


class Table:
    """Representa una tabla en memoria con esquema tipado y filas.

    La tabla no persiste datos en disco. Sus atributos ``columns`` y ``rows``
    ofrecen las operaciones sobre el esquema y los registros respectivamente.
    """

    def __init__(
        self,
        name: str,
        columns: dict[str, Any],
    ) -> None:
        """Crea una tabla con nombre no vacío y un esquema no vacío.

        Args:
            name: Nombre descriptivo de la tabla.
            columns: Diccionario de nombres de columna y anotaciones válidas.

        Raises:
            ValueError: Si el nombre no es una cadena no vacía, o el esquema
                no contiene columnas o tiene nombres inválidos.
            TypeError: Si alguna anotación de columna no es compatible.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Table name must be a non-empty string.")

        self.name = name

        # Shared internal storage.
        storage: list[dict[str, Any]] = []

        self.columns = Columns(columns, storage)
        self.rows = Rows(self.columns, storage)

    def clear(self) -> None:
        """Elimina todos los registros y conserva el esquema de columnas."""
        self.rows.clear()

    def __len__(self) -> int:
        """Devuelve la cantidad actual de filas."""
        return len(self.rows)

    def __repr__(self) -> str:
        """Devuelve una representación con nombre, columnas y cantidad."""
        return (
            f"Table(name={self.name!r}, "
            f"columns={list(self.columns.get_all())!r}, "
            f"rows={len(self.rows)})"
        )
