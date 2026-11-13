# API reference

This reference documents each public symbol: `Table`, `Columns`, `Rows`,
`TypeValidator`, and the package version. The [user guide](guide.md)
introduces them with examples.

```python
from ramtable import Columns, Rows, Table, __version__
from ramtable.types import TypeValidator
```

You normally create only a `Table`; it builds the matching `Columns` and
`Rows`.

## Contents

- [`Table`](#table)
- [`Columns`](#columns)
- [`Rows`](#rows)
- [`TypeValidator`](#typevalidator)
- [Package version](#package-version)
- [Internal helpers](#internal-helpers)
- [Copying behavior](#copying-behavior)

## Package version

```python
from ramtable import __version__
```

`__version__` is the version of the installed distribution, read from its
package metadata. It matches `project.version` in `pyproject.toml` and the
artifact built from it. In a source checkout that has not been installed,
it is `"0+unknown"`.

## `Table`

```python
Table(
    name: str,
    columns: dict[str, Any],
    defaults: dict[str, Any] | None = None,
)
```

A named table with a typed schema and rows. Data lives only in memory.
`table.columns` and `table.rows` share one record store.

### Constructor

**Arguments**

- `name`: descriptive name. Must be a non-empty string and cannot consist
  only of whitespace.
- `columns`: non-empty dictionary mapping each column name to an
  annotation supported by `TypeValidator`.
- `defaults`: optional dictionary mapping existing column names to values
  used when an inserted row omits that column. RAMTable validates each
  default against its column type and stores a deep copy.

**Raises**

- `ValueError`: invalid table name, schema that is not a non-empty
  dictionary, an invalid column name, or a default for a column that does
  not exist.
- `TypeError`: unsupported column annotation, `defaults` that is not a
  dictionary, a default that does not match its column type, or a default
  that cannot be deep-copied.

### `Table.clear() -> None`

Remove every row, as `rows.clear()` does. The name, schema, and insert
defaults stay.

### `len(table) -> int`

Return the current number of rows.

### `repr(table) -> str`

Return a debugging representation containing the name, column names, and
row count. Do not use it for serialization.

## `Columns`

Manages a table's column schema. `Table` passes a shallow copy of the
initial schema and the shared row storage.

### Constructor

```python
Columns(
    columns: dict[str, Any],
    rows_storage: list[dict[str, Any]],
    defaults: dict[str, Any] | None = None,
)
```

Create the schema. RAMTable rejects an empty schema, a name that is not a
non-empty string, and a type that `TypeValidator` does not support. It
validates and deep-copies optional defaults.

**Arguments**

- `columns`: mapping from column names to type annotations.
- `rows_storage`: storage shared with `Rows`.
- `defaults`: optional mapping of column names to insert defaults.

**Raises**

- `ValueError`: schema that is not a non-empty dictionary, an invalid
  column name, or a default for a column that does not exist.
- `TypeError`: unsupported annotation, `defaults` that is not a
  dictionary, a default that does not match its column type, or a default
  that cannot be deep-copied.

This constructor is primarily used internally by `Table`.

### `Columns.add(name, column_type, fill_value=..., *, default=...) -> None`

Add a column to the schema.

**Arguments**

- `name`: new non-empty column name.
- `column_type`: supported annotation for the column.
- `fill_value`: value for existing rows. Required when rows exist; RAMTable
  validates it against `column_type` and deep-copies it for each row. On an
  empty table RAMTable does not store it.
- `default`: optional insert default for future rows. Keyword-only. It is
  independent of `fill_value`: RAMTable validates and deep-copies it even
  when the table is empty, and providing it does not satisfy the
  `fill_value` requirement.

**Raises**

- `ValueError`: invalid or duplicate name, or a missing fill value when
  rows exist.
- `TypeError`: unsupported annotation, incompatible fill value or default,
  or a value that cannot be deep-copied.

RAMTable validates and prepares both values before changing any row or the
schema. If either fails, it adds no column and leaves the table unchanged.

### `Columns.remove(name) -> None`

Remove a column from the schema, its insert default, and the corresponding
key from every row.

**Arguments**

- `name`: existing column name.

**Raises**

- `ValueError`: the column does not exist or is the last column.

### `Columns.update(name, new_type) -> None`

Change a column's annotation without converting its values.

**Arguments**

- `name`: existing column name.
- `new_type`: annotation supported by `TypeValidator`.

RAMTable checks every current value and the insert default, if any, before
changing the schema. All must match `new_type`.

**Raises**

- `ValueError`: the column does not exist.
- `TypeError`: the new annotation is unsupported, or an existing value or
  the insert default does not match it.

### `Columns.get(name) -> Any`

Return the annotation associated with `name`.

**Raises:** `ValueError` if the column does not exist.

### `Columns.set_default(name, value) -> None`

Set or replace the insert default for a column. Future inserts that omit the
column use a deep copy of `value`.

**Arguments**

- `name`: existing column name.
- `value`: value compatible with the column's declared type.

**Raises**

- `ValueError`: the column does not exist.
- `TypeError`: the value does not match the column type or cannot be
  deep-copied.

The existing default, if any, stays in place when validation or copying
fails.

### `Columns.remove_default(name) -> None`

Remove a column's insert default. Future inserts must then include that
column.

**Arguments**

- `name`: existing column name with an insert default.

**Raises:** `ValueError` if the column does not exist or has no insert
default.

### `Columns.get_default(name) -> Any`

Return a deep copy of the insert default associated with `name`.

**Arguments**

- `name`: existing column name with an insert default.

**Raises**

- `ValueError`: the column does not exist or has no insert default.
- `TypeError`: the stored default cannot be deep-copied.

### `Columns.get_defaults() -> dict[str, Any]`

Return a new dictionary with deep copies of every insert default. The
dictionary is empty when no column has a default.

**Raises:** `TypeError` if a stored default cannot be deep-copied.

### `Columns.get_all() -> dict[str, Any]`

Return a shallow copy of the schema dictionary. Changes to the returned
dictionary leave the schema untouched.

### `name in columns -> bool`

Return whether the name is present in the schema.

### `len(columns) -> int`

Return the number of columns.

### `repr(columns) -> str`

Return a debugging representation of the schema.

## `Rows`

Manages rows against a `Columns` instance. `Table` constructs it with the
shared storage.

### Constructor

```python
Rows(columns: Columns, storage: list[dict[str, Any]])
```

**Arguments**

- `columns`: schema used to validate rows.
- `storage`: shared list used to store records.

This constructor is primarily used internally by `Table`.

### Filter conditions

`filter()`, `delete()`, and `update()` share one condition format. A
condition dictionary maps existing column names to one of:

- a plain value, compared with `==`;
- a dictionary of operators, all of which must match;
- a callable that receives the cell value and returns a truthy result.

| Operator | Meaning |
|---|---|
| `==` | equal to the operand |
| `!=` | different from the operand |
| `>`, `>=`, `<`, `<=` | ordered comparison |
| `in` | value is contained in the operand |
| `not_in` | value is not contained in the operand |
| `contains` | operand is contained in the value |
| `startswith` | string value starts with the operand |
| `endswith` | string value ends with the operand |

All entries are combined with AND. RAMTable does not validate condition
values against the declared column types; Python comparisons apply and may
raise `TypeError` for incompatible operands. RAMTable treats a dictionary
condition as an operator specification, so compare a column against a
dictionary value with `{"==": value}`.

**Raises** for any condition dictionary: `ValueError` if it is not a
non-empty dictionary, names a column that does not exist, or uses an
unknown operator.

### `Rows.insert(row) -> None`

Validate and append a shallow copy of `row`, filling omitted columns from
the table's insert defaults.

**Arguments**

- `row`: dictionary containing the schema keys and values compatible with
  their declared types. You may omit columns with an insert default.

**Raises**

- `TypeError`: `row` is not a dictionary, or a value does not match its
  type.
- `ValueError`: keys without an insert default are missing, or keys are
  undeclared.

The copy is shallow, so mutable values stay shared. RAMTable deep-copies an
insert default for each row that omits the column.

### `Rows.remove(row) -> None`

Validate `row` and remove the first row equal to it according to Python
equality.

**Arguments**

- `row`: dictionary with the keys and values required by the schema.

**Raises**

- `TypeError`: the row object or a value is incompatible.
- `ValueError`: the structure is invalid, or no equal row exists.

### `Rows.delete(where) -> int`

Delete every row that matches `where` (see
[filter conditions](#filter-conditions)). To remove one specific row by its
full content, use `remove` instead.

**Arguments**

- `where`: non-empty dictionary mapping column names to conditions.

**Returns**

- Number of deleted rows, zero when none match.

**Raises**

- `ValueError`: `where` is not a non-empty dictionary, names a non-existent
  column, or uses an unknown operator.

### `Rows.update(where, values) -> int`

Update every row that matches all conditions in `where` (see
[filter conditions](#filter-conditions)). Plain values still mean equality.

**Arguments**

- `where`: non-empty dictionary mapping existing column names to
  conditions. Condition values are not checked against the column types.
- `values`: non-empty dictionary mapping existing column names to new
  values. RAMTable checks each value against its declared type.

**Returns**

- Number of updated rows, zero when none match.

**Raises**

- `ValueError`: either argument is empty or is not a dictionary, or a
  non-existent column or filter operator is named.
- `TypeError`: a new value does not match its column type.

RAMTable validates the arguments and finds matches before changing any
row. Comparisons do not enforce types.

### `Rows.filter(where) -> list[dict[str, Any]]`

Return shallow copies of the rows that match `where` (see
[filter conditions](#filter-conditions)), in storage order.

**Arguments**

- `where`: non-empty dictionary mapping column names to conditions.

**Returns**

- A new list of shallow row copies; empty when nothing matches.

**Raises**

- `ValueError`: `where` is not a non-empty dictionary, names a non-existent
  column, or uses an unknown operator.

### `Rows.clear() -> None`

Remove all rows while preserving the schema and insert defaults.

### `Rows.get(*indexes) -> list[dict[str, Any]]`

With no arguments, return all rows. With indexes, return a shallow copy of
each requested row, in argument order.

**Arguments**

- `indexes`: zero or more integer indexes. Negative and repeated indexes
  are supported; `bool` is rejected.

**Raises**

- `TypeError`: an index is not an integer or is a boolean.
- `IndexError`: an index is out of range.

### `Rows.get_one(index) -> dict[str, Any]`

Return a shallow copy of one row.

**Arguments**

- `index`: integer index, positive or negative. Cannot be `bool`.

**Raises**

- `TypeError`: the index is not an integer or is a boolean.
- `IndexError`: the index is out of range.

### `Rows.get_all() -> list[dict[str, Any]]`

Return a new list containing a shallow copy of every row.

### `Rows.get_columns(*columns) -> dict[str, list[Any]]`

Return a list of values for each requested column name. With no arguments,
return every column in the schema.

**Arguments**

- `columns`: names of existing columns. Duplicate names are allowed; each
  key appears only once in the returned dictionary.

**Returns**

- New dictionary of column names to new lists. RAMTable copies the lists
  but not the values.

**Raises:** `ValueError` if a requested name does not exist.

### `Rows.get_column(column) -> list[Any]`

Return a new list containing all values from one column. RAMTable does not
copy the values.

**Arguments**

- `column`: name of an existing column.

**Raises:** `ValueError` if the column does not exist.

### Iteration, length, and representation

- `len(rows) -> int`: current number of rows.
- `iter(rows)`: iterate over shallow copies of the rows.
- `repr(rows) -> str`: debugging representation containing the row count.

## `TypeValidator`

Class with class methods in `ramtable.types`. Import it with:

```python
from ramtable.types import TypeValidator
```

You rarely call it: RAMTable uses it to validate columns, rows, and
assigned values.

### `TypeValidator.is_supported_type(value_type) -> bool`

Return whether RAMTable can evaluate the annotation form. This does not
validate a particular value or run validators embedded in `Annotated`
metadata.

**Arguments**

- `value_type`: class or annotation to check.

**Returns**

- `True` if the annotation form is supported, otherwise `False`.

### `TypeValidator.matches_type(value, value_type) -> bool`

Check whether a value matches a supported annotation. RAMTable checks
parameterized containers recursively. Simple classes use `isinstance`;
`Literal` compares both value and exact type. The value is not converted.

**Arguments**

- `value`: object to validate.
- `value_type`: supported class or annotation.

**Returns**

- `True` if the value matches, otherwise `False`. If a class annotation
  cannot be used with `isinstance`, this method returns `False`.

See [types and validation](types-and-validation.md) for supported
annotations and comparison details.

## Internal helpers

Implementation details, outside the stable API:

- `Columns._validate_name(name)`: checks that a name is a non-empty string
  containing non-whitespace characters; raises `ValueError` otherwise.
- `Columns._validate_type(column_type)`: checks an annotation with
  `TypeValidator`; raises `TypeError` if unsupported.
- `Rows._validate(row)`: checks the object type, the exact set of columns,
  and each value; raises `TypeError` or `ValueError` depending on the
  failure.
- `Rows._filter(where)`: validates a condition dictionary and returns the
  stored rows that match it. Shared by `filter`, `delete`, and `update`;
  returned rows are internal references, not copies.
- `Columns._insert_defaults(provided)`: returns deep copies of the insert
  defaults for columns not listed in `provided`. `Rows.insert` passes the
  columns already present in the row.

## Copying behavior

RAMTable shallow-copies the schema and returned row dictionaries.
`get_columns` and `get_column` return new lists and dictionaries, but their
items keep their identity.

`Columns.add` deep-copies `fill_value` for each existing record. Insert
defaults are deep-copied when set, each time a row omits the column, and
when `Columns.get_default` or `Columns.get_defaults` returns them.
