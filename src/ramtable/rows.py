
"""Row insertion, retrieval, filtering, update, and removal operations."""

from typing import Any, Callable

from .columns import Columns
from .types import TypeValidator

_FILTER_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "==": lambda value, operand: value == operand,
    "!=": lambda value, operand: value != operand,
    ">": lambda value, operand: value > operand,
    ">=": lambda value, operand: value >= operand,
    "<": lambda value, operand: value < operand,
    "<=": lambda value, operand: value <= operand,
    "in": lambda value, operand: value in operand,
    "not_in": lambda value, operand: value not in operand,
    "contains": lambda value, operand: operand in value,
    "startswith": lambda value, operand: value.startswith(operand),
    "endswith": lambda value, operand: value.endswith(operand),
}


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

    def _filter(self, where: dict[str, Any]) -> list[dict[str, Any]]:
        """Return the stored rows that satisfy every condition in ``where``.

        This is the shared engine behind :meth:`filter`, :meth:`delete`, and
        :meth:`update`. Each key is a column name and each condition is one
        of:

        * a plain value, matched with ``==``;
        * a dictionary of operators whose operands must all match;
        * a callable that receives the cell value and returns a truthy
          result when the row matches.

        Supported operators are ``==``, ``!=``, ``>``, ``>=``, ``<``,
        ``<=``, ``in``, ``not_in``, ``contains``, ``startswith``, and
        ``endswith``. All conditions are combined with ``and``.

        Returned rows are internal references; callers copy them before
        exposing them outside the class.

        Raises:
            ValueError: If ``where`` is not a non-empty dictionary, names a
                column that does not exist, or uses an unknown operator.
        """

        if not isinstance(where, dict) or not where:
            raise ValueError(
                "Filter conditions must be a non-empty dictionary."
            )

        schema = self._columns.get_all()

        for column, condition in where.items():
            if column not in schema:
                raise ValueError(f"Column '{column}' does not exist.")

            if isinstance(condition, dict):
                if not condition:
                    raise ValueError(
                        f"Filter for column '{column}' must not be empty."
                    )

                for operator in condition:
                    if operator not in _FILTER_OPERATORS:
                        raise ValueError(
                            f"Unknown filter operator {operator!r}. "
                            "Supported operators: "
                            f"{', '.join(_FILTER_OPERATORS)}."
                        )

        def matches(value: Any, condition: Any) -> bool:
            if isinstance(condition, dict):
                return all(
                    _FILTER_OPERATORS[operator](value, operand)
                    for operator, operand in condition.items()
                )

            if callable(condition) and not isinstance(condition, type):
                return bool(condition(value))

            return value == condition

        return [
            row
            for row in self._storage
            if all(
                matches(row[column], condition)
                for column, condition in where.items()
            )
        ]

    def insert(self, row: dict[str, Any]) -> None:
        """Validate and append a shallow copy of ``row``.

        Columns omitted from ``row`` are filled from the table's insert
        defaults when available. Columns without a default remain required.

        Raises:
            TypeError: If the row or one of its values is invalid.
            ValueError: If the row does not have exactly the schema columns
                after insert defaults are applied.
        """

        if not isinstance(row, dict):
            raise TypeError("Row must be a dictionary.")

        completed = row.copy()

        for name, value in self._columns._insert_defaults().items():
            if name not in completed:
                completed[name] = value

        self._validate(completed)
        self._storage.append(completed)

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

    def delete(self, where: dict[str, Any]) -> int:
        """Delete every row that matches ``where``.

        Conditions use the same format as :meth:`filter` and :meth:`update`.
        To remove one specific row by its full content, use :meth:`remove`.

        Args:
            where: Non-empty dictionary mapping column names to conditions.

        Returns:
            Number of deleted rows; may be zero.

        Raises:
            ValueError: If ``where`` is not a non-empty dictionary, names a
                column that does not exist, or uses an unknown operator.
        """

        matches = self._filter(where)

        if matches:
            matched = {id(row) for row in matches}
            self._storage[:] = [
                row for row in self._storage
                if id(row) not in matched
            ]

        return len(matches)

    def update(
        self,
        where: dict[str, Any],
        values: dict[str, Any],
    ) -> int:
        """Update fields in every row that satisfies ``where``.

        Both ``where`` and ``values`` must be non-empty dictionaries containing
        existing column names. Conditions use the same flexible format as
        :meth:`filter`; new values are validated against the schema, but
        condition values are not. The entire request is validated before any
        rows are modified.

        Args:
            where: Conditions that a row must satisfy (see :meth:`filter`).
            values: Columns and values to assign to each matching row.

        Returns:
            Number of updated rows; may be zero.

        Raises:
            TypeError: If an assigned value does not match its column type.
            ValueError: If either argument is empty or not a dictionary, or
                if a non-existent column or filter operator is named.
        """

        if not isinstance(values, dict) or not values:
            raise ValueError(
                "Update values must be a non-empty dictionary."
            )

        schema = self._columns.get_all()

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

        # Find matching rows before modifying anything. ``_filter`` validates
        # the conditions and returns references to stored rows.
        matching_rows = self._filter(where)

        # Apply changes.
        for row in matching_rows:
            row.update(values)

        return len(matching_rows)

    def filter(self, where: dict[str, Any]) -> list[dict[str, Any]]:
        """Return shallow copies of the rows that match ``where``.

        Conditions use the same format as :meth:`update` and :meth:`delete`;
        see :meth:`_filter` for the supported operators and callables. Rows
        are returned in storage order.

        Args:
            where: Non-empty dictionary mapping column names to conditions.

        Returns:
            New list of shallow row copies; empty when nothing matches.

        Raises:
            ValueError: If ``where`` is not a non-empty dictionary, names a
                column that does not exist, or uses an unknown operator.
        """

        return [row.copy() for row in self._filter(where)]

    def clear(self) -> None:
        """Remove all rows without changing the schema."""
        self._storage.clear()

    def get(self, *indexes: int) -> list[dict[str, Any]]:
        """Return all rows or copies of the requested positions.

        With no arguments, return all rows. Indexes support negative values as
        Python lists do; the requested order is preserved and repeated
        indexes are allowed.

        Raises:
            TypeError: If an index is not an integer or is a boolean.
            IndexError: If an index is out of range.
        """

        if not indexes:
            return self.get_all()

        selected = []

        for index in indexes:
            if isinstance(index, bool) or not isinstance(index, int):
                raise TypeError("Row indexes must be integers.")

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
