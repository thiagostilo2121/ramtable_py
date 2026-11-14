
"""Main container coordinating a table's schema and rows."""

from typing import Any

from .columns import Columns
from .rows import Rows


class Table:
    """Represent an in-memory table with a typed schema and rows.

    The table does not persist data to disk. Its ``columns`` and ``rows``
    attributes provide operations on the schema and records, respectively.
    """

    def __init__(
        self,
        name: str,
        columns: dict[str, Any],
        defaults: dict[str, Any] | None = None,
    ) -> None:
        """Create a table with a non-empty name and schema.

        Args:
            name: Descriptive table name.
            columns: Dictionary of column names and supported annotations.
            defaults: Optional mapping of column names to values used when
                an inserted row omits that column.

        Raises:
            ValueError: If the name is not a non-empty string, the schema is
                empty, a column name is invalid, or a default names an
                unknown column.
            TypeError: If a column annotation is unsupported, the defaults
                are not a dictionary, or a default does not match its type.
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Table name must be a non-empty string.")

        self.name = name

        # Shared internal storage.
        storage: list[dict[str, Any]] = []

        self.columns = Columns(columns, storage, defaults)
        self.rows = Rows(self.columns, storage)

    def clear(self) -> None:
        """Remove all records while preserving the name, schema, and
        defaults.
        """
        self.rows.clear()

    def __len__(self) -> int:
        """Return the current number of rows."""
        return len(self.rows)

    def __repr__(self) -> str:
        """Return a debugging representation of the table.

        The result contains the name, column names, and row count. Do not
        use it for serialization.
        """
        return (
            f"Table(name={self.name!r}, "
            f"columns={list(self.columns.get_all())!r}, "
            f"rows={len(self.rows)})"
        )
