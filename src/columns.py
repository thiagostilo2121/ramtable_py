
"""Esquema mutable de columnas y validación de sus cambios."""

from copy import deepcopy
from typing import Any

from .types import TypeValidator

_MISSING = object()


class Columns:
    """Administra los nombres y tipos asociados a las columnas de una tabla.

    La instancia mantiene una copia del esquema recibido y comparte el
    almacenamiento de filas de la tabla propietaria para aplicar cambios al
    esquema de forma coherente con los registros existentes.
    """

    def __init__(
        self,
        columns: dict[str, Any],
        rows_storage: list[dict[str, Any]],
    ) -> None:
        """Crea un esquema no vacío asociado al almacenamiento de filas.

        Args:
            columns: Mapa entre cada nombre de columna y su tipo admitido.
            rows_storage: Lista compartida de registros de la tabla.

        Raises:
            ValueError: Si el esquema está vacío o un nombre no es válido.
            TypeError: Si alguna anotación de tipo no está admitida.
        """
        if not isinstance(columns, dict) or not columns:
            raise ValueError("Table must have at least one column.")

        self._columns = columns.copy()
        self._rows_storage = rows_storage

        for name, column_type in self._columns.items():
            self._validate_name(name)
            self._validate_type(column_type)

    @staticmethod
    def _validate_name(name: str) -> None:
        """Rechaza nombres de columna que no sean cadenas no vacías."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Column names must be non-empty strings.")

    @staticmethod
    def _validate_type(column_type: object) -> None:
        """Rechaza anotaciones que el validador de RAMTable no admite."""
        if not TypeValidator.is_supported_type(column_type):
            raise TypeError(
                f"Unsupported column type: {column_type!r}"
            )

    def add(
        self,
        name: str,
        column_type: Any,
        default: Any = _MISSING,
    ) -> None:
        """Añade una columna y, si corresponde, la inicializa en las filas.

        Cuando ya hay registros, ``default`` es obligatorio. Se crea una
        copia profunda del valor por cada registro para que los valores
        mutables predeterminados no se compartan entre filas. Si no hay filas,
        el valor predeterminado opcional no se almacena.

        Raises:
            ValueError: Si el nombre está vacío, ya existe o falta un valor
                predeterminado requerido.
            TypeError: Si el tipo o el valor predeterminado no son válidos.
        """

        self._validate_name(name)
        self._validate_type(column_type)

        if name in self._columns:
            raise ValueError(f"Column '{name}' already exists.")

        if self._rows_storage and default is _MISSING:
            raise ValueError(
                "A default value is required when adding a column "
                "to a table containing rows."
            )

        if default is not _MISSING:
            if not TypeValidator.matches_type(default, column_type):
                raise TypeError(
                    f"Default value does not match {column_type!r}."
                )

        # Prepare all default values before changing the table.
        # This prevents partial updates if copying fails.
        if self._rows_storage:
            default_values = [
                deepcopy(default) for _ in self._rows_storage
            ]

            for row, value in zip(self._rows_storage, default_values):
                row[name] = value

        self._columns[name] = column_type

    def remove(self, name: str) -> None:
        """Elimina una columna del esquema y de todos los registros.

        Raises:
            ValueError: Si la columna no existe o es la última columna.
        """

        if name not in self._columns:
            raise ValueError(f"Column '{name}' does not exist.")

        if len(self._columns) == 1:
            raise ValueError(
                "A table must have at least one column."
            )

        for row in self._rows_storage:
            del row[name]

        del self._columns[name]

    def update(self, name: str, new_type: Any) -> None:
        """Cambia el tipo declarado si todos los valores actuales coinciden.

        No convierte los valores almacenados. El cambio se aplica solo después
        de validar todos los registros.

        Raises:
            ValueError: Si la columna no existe.
            TypeError: Si el nuevo tipo no se admite o algún valor actual no
                satisface el tipo nuevo.
        """

        if name not in self._columns:
            raise ValueError(f"Column '{name}' does not exist.")

        self._validate_type(new_type)

        for row in self._rows_storage:
            value = row[name]

            if not TypeValidator.matches_type(value, new_type):
                raise TypeError(
                    f"Existing value in column '{name}' "
                    f"does not match {new_type!r}."
                )

        self._columns[name] = new_type

    def get(self, name: str) -> Any:
        """Devuelve la anotación de tipo de una columna.

        Raises:
            ValueError: Si la columna no existe.
        """

        if name not in self._columns:
            raise ValueError(f"Column '{name}' does not exist.")

        return self._columns[name]

    def get_all(self) -> dict[str, Any]:
        """Devuelve una copia superficial del esquema completo."""
        return self._columns.copy()

    def __contains__(self, name: str) -> bool:
        """Indica si ``name`` está declarado en el esquema."""
        return name in self._columns

    def __len__(self) -> int:
        """Devuelve la cantidad de columnas declaradas."""
        return len(self._columns)

    def __repr__(self) -> str:
        """Devuelve una representación orientada a depuración del esquema."""
        return f"Columns({self._columns!r})"
