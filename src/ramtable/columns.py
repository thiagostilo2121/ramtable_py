
"""Mutable column schema and validation of schema changes."""

from copy import deepcopy
from typing import Any

from .types import TypeValidator

_MISSING = object()


class Columns:
    """Manage the names and types associated with a table's columns.

    The instance keeps a copy of the supplied schema and shares its owning
    table's row storage so schema changes remain consistent with existing
    records.
    """

    def __init__(
        self,
        columns: dict[str, Any],
        rows_storage: list[dict[str, Any]],
    ) -> None:
        """Create a non-empty schema associated with row storage.

        Args:
            columns: Mapping of column names to supported types.
            rows_storage: Shared list of table records.

        Raises:
            ValueError: If the schema is empty or a name is invalid.
            TypeError: If a type annotation is unsupported.
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
        """Reject column names that are not non-empty strings."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Column names must be non-empty strings.")

    @staticmethod
    def _validate_type(column_type: object) -> None:
        """Reject annotations unsupported by RAMTable's type validator."""
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
        """Add a column and initialize existing rows when necessary.

        If records already exist, ``default`` is required. A deep copy of the
        value is created for each record so mutable defaults are not shared
        between rows. If there are no rows, an optional default is not stored.

        Raises:
            ValueError: If the name is empty, already exists, or a required
                default is missing.
            TypeError: If the type or default value is invalid.
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
        """Remove a column from the schema and all records.

        Raises:
            ValueError: If the column does not exist or is the last column.
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
        """Change a column's declared type if all current values match.

        Stored values are not converted. The change is applied only after
        every record has been validated.

        Raises:
            ValueError: If the column does not exist.
            TypeError: If the new type is unsupported or any current value
                does not match it.
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
        """Return the type annotation of a column.

        Raises:
            ValueError: If the column does not exist.
        """

        if name not in self._columns:
            raise ValueError(f"Column '{name}' does not exist.")

        return self._columns[name]

    def get_all(self) -> dict[str, Any]:
        """Return a shallow copy of the complete schema."""
        return self._columns.copy()

    def __contains__(self, name: str) -> bool:
        """Return whether ``name`` is declared in the schema."""
        return name in self._columns

    def __len__(self) -> int:
        """Return the number of declared columns."""
        return len(self._columns)

    def __repr__(self) -> str:
        """Return a debugging representation of the schema."""
        return f"Columns({self._columns!r})"
