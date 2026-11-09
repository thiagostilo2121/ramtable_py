
"""Operaciones de inserción, consulta, actualización y borrado de filas."""

from typing import Any

from .columns import Columns
from .types import TypeValidator


class Rows:
    """Proporciona operaciones sobre las filas de una tabla.

    Las filas se almacenan como diccionarios en un almacenamiento compartido
    con :class:`Columns`. Las copias devueltas son superficiales: los
    diccionarios son nuevos, pero los objetos mutables que contienen pueden
    seguir compartidos.
    """

    def __init__(
        self,
        columns: Columns,
        storage: list[dict[str, Any]],
    ) -> None:
        """Vincula la vista de filas con el esquema y el almacenamiento.

        Args:
            columns: Esquema que cada fila debe satisfacer.
            storage: Lista compartida en la que se guardan las filas.
        """
        self._columns = columns
        self._storage = storage

    def _validate(self, row: dict[str, Any]) -> None:
        """Valida que una fila tenga todas las columnas y tipos correctos.

        Raises:
            TypeError: Si ``row`` no es un diccionario o un valor no coincide
                con el tipo declarado.
            ValueError: Si faltan columnas o hay columnas no declaradas.
        """
        if not isinstance(row, dict):
            raise TypeError("Row must be a dictionary.")

        schema = self._columns.get_all()

        expected = set(schema)
        received = set(row)

        if expected != received:
            missing = expected - received
            unexpected = received - expected

            raise ValueError(
                f"Invalid row structure. "
                f"Missing columns: {missing}. "
                f"Unexpected columns: {unexpected}."
            )

        for column, column_type in schema.items():
            if not TypeValidator.matches_type(
                row[column], column_type
            ):
                raise TypeError(
                    f"Invalid value for column '{column}'. "
                    f"Expected {column_type!r}, "
                    f"received {type(row[column]).__name__}."
                )

    def insert(self, row: dict[str, Any]) -> None:
        """Valida e inserta una copia superficial de ``row`` al final.

        Raises:
            TypeError: Si la fila o alguno de sus valores no es válido.
            ValueError: Si la fila no tiene exactamente las columnas del
                esquema.
        """

        self._validate(row)
        self._storage.append(row.copy())

    def remove(self, row: dict[str, Any]) -> None:
        """Elimina la primera fila igual a ``row`` tras validar su estructura.

        Raises:
            TypeError: Si la fila o alguno de sus valores no es válido.
            ValueError: Si la fila no coincide con el esquema o no existe.
        """

        self._validate(row)

        try:
            self._storage.remove(row)
        except ValueError:
            raise ValueError(
                "Row does not exist in this table."
            ) from None


    def update(
        self,
        where: dict[str, Any],
        values: dict[str, Any],
    ) -> int:
        """Actualiza campos de todas las filas que satisfacen ``where``.

        Tanto ``where`` como ``values`` deben ser diccionarios no vacíos y
        nombrar columnas existentes. Los valores nuevos se validan según el
        esquema; las condiciones se comparan por igualdad y sus valores no se
        validan contra el tipo de la columna. La operación valida toda la
        solicitud antes de modificar filas.

        Args:
            where: Condiciones de igualdad que deben cumplirse en una fila.
            values: Columnas y valores que se asignarán a cada coincidencia.

        Returns:
            Cantidad de filas actualizadas; puede ser cero.

        Raises:
            TypeError: Si un valor a asignar no coincide con su tipo.
            ValueError: Si alguno de los argumentos es vacío/no es un
                diccionario o se nombra una columna inexistente.
        """

        if not isinstance(where, dict) or not where:
            raise ValueError(
                "Update conditions must be a non-empty dictionary."
            )

        if not isinstance(values, dict) or not values:
            raise ValueError(
                "Update values must be a non-empty dictionary."
            )

        schema = self._columns.get_all()

        # Validate condition columns.
        for column in where:
            if column not in schema:
                raise ValueError(
                    f"Column '{column}' does not exist."
                )

        # Validate update columns and their values.
        for column, value in values.items():
            if column not in schema:
                raise ValueError(
                    f"Column '{column}' does not exist."
                )

            if not TypeValidator.matches_type(value, schema[column]):
                raise TypeError(
                    f"Invalid value for column '{column}'. "
                    f"Expected {schema[column]!r}, "
                    f"received {type(value).__name__}."
                )

        # Find matching rows before modifying anything.
        matching_rows = [
            row for row in self._storage
            if all(row[column] == value for column, value in where.items())
        ]

        # Apply changes.
        for row in matching_rows:
            row.update(values)

        return len(matching_rows)


    def clear(self) -> None:
        """Elimina todas las filas sin modificar el esquema."""
        self._storage.clear()

    def get(self, *indices: int) -> list[dict[str, Any]]:
        """Devuelve todas las filas o copias de las posiciones solicitadas.

        Sin argumentos, devuelve todas las filas. Los índices admiten valores
        negativos como las listas de Python; se conserva el orden y se
        permiten índices repetidos.

        Raises:
            TypeError: Si un índice no es un entero o es un booleano.
            IndexError: Si alguno de los índices está fuera de rango.
        """

        if not indices:
            return self.get_all()

        selected = []

        for index in indices:
            if isinstance(index, bool) or not isinstance(index, int):
                raise TypeError("Row indices must be integers.")

            try:
                selected.append(self._storage[index].copy())
            except IndexError:
                raise IndexError(
                    f"Row index {index} is out of range."
                ) from None

        return selected

    def get_one(self, index: int) -> dict[str, Any]:
        """Devuelve una copia superficial de la fila en ``index``.

        Admite índices negativos. ``bool`` no se acepta como índice, aunque
        sea una subclase de ``int`` en Python.

        Raises:
            TypeError: Si el índice no es entero o es un booleano.
            IndexError: Si el índice está fuera de rango.
        """

        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError("Row index must be an integer.")

        try:
            return self._storage[index].copy()
        except IndexError:
            raise IndexError(
                f"Row index {index} is out of range."
            ) from None

    def get_all(self) -> list[dict[str, Any]]:
        """Devuelve una lista nueva con una copia superficial de cada fila."""
        return [row.copy() for row in self._storage]

    def get_columns(self, *columns: str) -> dict[str, list[Any]]:
        """Devuelve listas de valores para las columnas solicitadas.

        Si no se indican nombres, incluye todas las columnas del esquema. El
        diccionario y las listas son nuevos, pero los valores no se copian.

        Raises:
            ValueError: Si se solicita una columna inexistente.
        """

        schema = self._columns.get_all()

        if not columns:
            columns = tuple(schema.keys())

        result = {}

        for column in columns:
            if column not in schema:
                raise ValueError(f"Column '{column}' does not exist.")

            result[column] = [
                row[column] for row in self._storage
            ]

        return result

    def get_column(self, column: str) -> list[Any]:
        """Devuelve una lista nueva con los valores de una columna.

        Los valores no se copian.

        Raises:
            ValueError: Si la columna no existe.
        """

        if column not in self._columns:
            raise ValueError(f"Column '{column}' does not exist.")

        return [
            row[column] for row in self._storage
        ]

    def __len__(self) -> int:
        """Devuelve la cantidad actual de filas."""
        return len(self._storage)

    def __iter__(self):
        """Itera sobre copias superficiales de las filas actuales."""
        return iter(self.get_all())

    def __repr__(self) -> str:
        """Devuelve una representación breve con el número de filas."""
        return f"Rows(count={len(self)})"
