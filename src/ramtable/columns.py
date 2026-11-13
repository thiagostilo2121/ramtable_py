
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
        defaults: dict[str, Any] | None = None,
    ) -> None:
        """Create a non-empty schema associated with row storage.

        Args:
            columns: Mapping of column names to supported types.
            rows_storage: Shared list of table records.
            defaults: Optional mapping of column names to values used when
                an inserted row omits that column.

        Raises:
            ValueError: If the schema is empty, a name is invalid, or a
                default names an unknown column.
            TypeError: If a type annotation is unsupported, the defaults are
                not a dictionary, or a default does not match its type.
        """
        if not isinstance(columns, dict) or not columns:
            raise ValueError("Table must have at least one column.")

        self._columns = columns.copy()
        self._rows_storage = rows_storage

        for name, column_type in self._columns.items():
            self._validate_name(name)
            self._validate_type(column_type)

        if defaults is None:
            defaults = {}

        if not isinstance(defaults, dict):
            raise TypeError("Column defaults must be a dictionary.")

        for name, value in defaults.items():
            if name not in self._columns:
                raise ValueError(
                    f"Default value provided for unknown column '{name}'."
                )

            self._validate_default(name, value, self._columns[name])

        self._defaults: dict[str, Any] = {}

        for name, value in defaults.items():
            self._defaults[name] = self._copy_default(name, value)

    @staticmethod
    def _validate_default(
        name: str,
        value: Any,
        column_type: Any,
    ) -> None:
        """Reject a default that does not match its column's annotation."""
        if not TypeValidator.matches_type(value, column_type):
            raise TypeError(
                f"Default value for column '{name}' does not match "
                f"{column_type!r}."
            )

    @staticmethod
    def _copy_default(name: str, value: Any) -> Any:
        """Return a deep copy of a default or raise a descriptive error."""
        try:
            return deepcopy(value)
        except Exception as error:
            raise TypeError(
                f"Default value for column '{name}' "
                "cannot be deep-copied."
            ) from error

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
        fill_value: Any = _MISSING,
        *,
        default: Any = _MISSING,
    ) -> None:
        """Add a column and initialize existing rows when necessary.

        If records already exist, ``fill_value`` is required. A deep copy of
        the value is created for each record so mutable values are not shared
        between rows. If there are no rows, an optional fill value is not
        stored.

        ``default`` is independent of ``fill_value``: it supplies the value
        used by future inserts that omit the column. It is validated and
        deep-copied even when the table is empty.

        Args:
            name: Column name.
            column_type: Supported type annotation.
            fill_value: Value assigned to existing rows when the table is
                not empty.
            default: Optional insert default for future rows. Keyword-only.

        Raises:
            ValueError: If the name is empty, already exists, or a required
                fill value is missing.
            TypeError: If the type, fill value, or default is invalid, or a
                value cannot be deep-copied.
        """

        self._validate_name(name)
        self._validate_type(column_type)

        if name in self._columns:
            raise ValueError(f"Column '{name}' already exists.")

        if self._rows_storage and fill_value is _MISSING:
            raise ValueError(
                "A fill value is required when adding a column "
                "to a table containing rows."
            )

        if (
            fill_value is not _MISSING
            and not TypeValidator.matches_type(fill_value, column_type)
        ):
            raise TypeError(
                f"Fill value does not match {column_type!r}."
            )

        default_copy = _MISSING

        if default is not _MISSING:
            self._validate_default(name, default, column_type)
            default_copy = self._copy_default(name, default)

        # Prepare all fill values before changing the table.
        # This prevents partial updates if copying fails.
        if self._rows_storage:
            try:
                fill_values = [
                    deepcopy(fill_value)
                    for _ in self._rows_storage
                ]
            except Exception as error:
                raise TypeError(
                    "Fill value cannot be deep-copied."
                ) from error

            for row, value in zip(self._rows_storage, fill_values):
                row[name] = value

        self._columns[name] = column_type

        if default_copy is not _MISSING:
            self._defaults[name] = default_copy

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
        self._defaults.pop(name, None)

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

        if name in self._defaults and not TypeValidator.matches_type(
            self._defaults[name], new_type
        ):
            raise TypeError(
                f"Default value for column '{name}' does not match "
                f"{new_type!r}."
            )

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

    def set_default(self, name: str, value: Any) -> None:
        """Set or replace a column's insert default.

        The value is validated against the column's declared type and stored
        as a deep copy. Future inserts that omit the column use it.

        Args:
            name: Existing column name.
            value: Value to use when an inserted row omits the column.

        Raises:
            ValueError: If the column does not exist.
            TypeError: If the value does not match the column type or cannot
                be deep-copied.
        """

        if name not in self._columns:
            raise ValueError(f"Column '{name}' does not exist.")

        self._validate_default(name, value, self._columns[name])
        copied = self._copy_default(name, value)
        self._defaults[name] = copied

    def remove_default(self, name: str) -> None:
        """Remove a column's insert default.

        Future inserts must provide the column explicitly.

        Raises:
            ValueError: If the column does not exist or has no default.
        """

        if name not in self._columns:
            raise ValueError(f"Column '{name}' does not exist.")

        if name not in self._defaults:
            raise ValueError(
                f"Column '{name}' does not have a default value."
            )

        del self._defaults[name]

    def get_default(self, name: str) -> Any:
        """Return a deep copy of a column's insert default.

        Raises:
            ValueError: If the column does not exist or has no default.
            TypeError: If the stored default cannot be deep-copied.
        """

        if name not in self._columns:
            raise ValueError(f"Column '{name}' does not exist.")

        if name not in self._defaults:
            raise ValueError(
                f"Column '{name}' does not have a default value."
            )

        return self._copy_default(name, self._defaults[name])

    def get_defaults(self) -> dict[str, Any]:
        """Return deep copies of every insert default.

        Returns:
            New dictionary mapping column names to default values.

        Raises:
            TypeError: If a stored default cannot be deep-copied.
        """

        return {
            name: self._copy_default(name, value)
            for name, value in self._defaults.items()
        }

    def get_all(self) -> dict[str, Any]:
        """Return a shallow copy of the complete schema."""
        return self._columns.copy()

    def _insert_defaults(
        self,
        provided: set[str],
    ) -> dict[str, Any]:
        """Return deep copies of defaults for columns not in ``provided``."""
        return {
            name: self._copy_default(name, value)
            for name, value in self._defaults.items()
            if name not in provided
        }

    def __contains__(self, name: str) -> bool:
        """Return whether ``name`` is declared in the schema."""
        return name in self._columns

    def __len__(self) -> int:
        """Return the number of declared columns."""
        return len(self._columns)

    def __repr__(self) -> str:
        """Return a debugging representation of the schema."""
        return f"Columns({self._columns!r})"
