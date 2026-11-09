
"""Row insertion, retrieval, update, and removal operations."""

from typing import Any

from .columns import Columns
from .types import TypeValidator


class Rows:
    """Provide operations on a table's rows.

    Rows are stored as dictionaries in storage shared with :class:`Columns`.
    Returned copies are shallow: the dictionaries are new, but mutable
    objects they contain may still be shared.
    """

    def __init__(
        self,
        columns: Columns,
        storage: list[dict[str, Any]],
    ) -> None:
        """Bind the row view to its schema and storage.

        Args:
            columns: Schema that each row must satisfy.
            storage: Shared list used to store rows.
        """
        self._columns = columns
        self._storage = storage

    def _validate(self, row: dict[str, Any]) -> None:
        """Validate that a row has exactly the required columns and types.

        Raises:
            TypeError: If ``row`` is not a dictionary or a value does not
                match its declared type.
            ValueError: If columns are missing or undeclared.
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
        """Validate and append a shallow copy of ``row``.

        Raises:
            TypeError: If the row or one of its values is invalid.
            ValueError: If the row does not have exactly the schema columns.
        """

        self._validate(row)
        self._storage.append(row.copy())

    def remove(self, row: dict[str, Any]) -> None:
        """Remove the first row equal to ``row`` after validating its shape.

        Raises:
            TypeError: If the row or one of its values is invalid.
            ValueError: If the row does not match the schema or does not exist.
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
        """Update fields in every row that satisfies ``where``.

        Both ``where`` and ``values`` must be non-empty dictionaries containing
        existing column names. New values are validated against the schema;
        conditions use equality and their values are not checked against the
        column type. The entire request is validated before any rows are
        modified.

        Args:
            where: Equality conditions that a row must satisfy.
            values: Columns and values to assign to each matching row.

        Returns:
            Number of updated rows; may be zero.

        Raises:
            TypeError: If an assigned value does not match its column type.
            ValueError: If either argument is empty or not a dictionary, or
                if a non-existent column is named.
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
        """Remove all rows without changing the schema."""
        self._storage.clear()

    def get(self, *indices: int) -> list[dict[str, Any]]:
        """Return all rows or copies of the requested positions.

        With no arguments, return all rows. Indexes support negative values as
        Python lists do; the requested order is preserved and repeated
        indexes are allowed.

        Raises:
            TypeError: If an index is not an integer or is a boolean.
            IndexError: If an index is out of range.
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
        """Return a shallow copy of the row at ``index``.

        Negative indexes are supported. ``bool`` is not accepted as an index,
        although it is a subclass of ``int`` in Python.

        Raises:
            TypeError: If the index is not an integer or is a boolean.
            IndexError: If the index is out of range.
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
        """Return a new list containing a shallow copy of each row."""
        return [row.copy() for row in self._storage]

    def get_columns(self, *columns: str) -> dict[str, list[Any]]:
        """Return value lists for the requested columns.

        If no names are given, include every schema column. The dictionary and
        lists are new, but their values are not copied.

        Raises:
            ValueError: If a requested column does not exist.
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
        """Return a new list containing the values of one column.

        Values are not copied.

        Raises:
            ValueError: If the column does not exist.
        """

        if column not in self._columns:
            raise ValueError(f"Column '{column}' does not exist.")

        return [
            row[column] for row in self._storage
        ]

    def __len__(self) -> int:
        """Return the current number of rows."""
        return len(self._storage)

    def __iter__(self):
        """Iterate over shallow copies of the current rows."""
        return iter(self.get_all())

    def __repr__(self) -> str:
        """Return a short representation with the number of rows."""
        return f"Rows(count={len(self)})"
