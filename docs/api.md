# API reference

This reference covers every public symbol RAMTable exposes: the `Table`,
`Columns`, and `Rows` classes, the optional `TypeValidator`, and the package
version. For an example-driven introduction, read the
[user guide](guide.md) first.

```python
from ramtable import Columns, Rows, Table, __version__
from ramtable.types import TypeValidator
```

In normal use you only create a `Table`; it constructs the coordinated
`Columns` and `Rows` instances for you.

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
Table(name: str, columns: dict[str, Any])
```

The main container: a named table with a typed schema and rows. Data is not
persistent. `table.columns` and `table.rows` are coordinated views that
share the same record storage.

### Constructor

**Arguments**

- `name`: descriptive name. Must be a non-empty string and cannot consist
  only of whitespace.
- `columns`: non-empty dictionary mapping each column name to an
  annotation supported by `TypeValidator`.

**Raises**

- `ValueError`: invalid table name, schema that is not a non-empty
  dictionary, or an invalid column name.
- `TypeError`: unsupported column annotation.

### `Table.clear() -> None`

Remove all records by calling `rows.clear()`. The table name and schema
are preserved.

### `len(table) -> int`

Return the current number of rows.

### `repr(table) -> str`

Return a debugging representation containing the name, column names, and
row count. This is not a serialization format.

## `Columns`

Manage a table's column schema. The instance created by `Table` keeps a
shallow copy of the initial schema dictionary and shares the table's row
storage.

### Constructor

```python
Columns(columns: dict[str, Any], rows_storage: list[dict[str, Any]])
```

Create the schema and validate that it is not empty, that every name is a
non-empty string, and that every type is supported by `TypeValidator`.

**Arguments**

- `columns`: mapping from column names to type annotations.
- `rows_storage`: storage shared with `Rows`.

**Raises**

- `ValueError`: schema that is not a non-empty dictionary, or an invalid
  column name.
- `TypeError`: unsupported annotation.

This constructor is primarily used internally by `Table`.

### `Columns.add(name, column_type, default=...) -> None`

Add a column to the schema.

**Arguments**

- `name`: new non-empty column name.
- `column_type`: supported annotation for the column.
- `default`: optional value. Required if rows already exist; it is
  validated against `column_type` and deep-copied separately for every row.
  If there are no rows, the default is not stored.

**Raises**

- `ValueError`: invalid or duplicate name, or a missing default when rows
  exist.
- `TypeError`: unsupported annotation or incompatible default.

Default values are prepared before any row is changed. If copying fails,
the column is not added.

### `Columns.remove(name) -> None`

Remove a column from the schema and the corresponding key from every row.

**Arguments**

- `name`: existing column name.

**Raises**

- `ValueError`: the column does not exist or is the last column.

### `Columns.update(name, new_type) -> None`

Change a column's annotation without converting its values.

**Arguments**

- `name`: existing column name.
- `new_type`: annotation supported by `TypeValidator`.

All current values are checked first. The schema is changed only if every
value matches `new_type`.

**Raises**

- `ValueError`: the column does not exist.
- `TypeError`: the new annotation is unsupported, or an existing value
  does not match it.

### `Columns.get(name) -> Any`

Return the annotation associated with `name`.

**Raises:** `ValueError` if the column does not exist.

### `Columns.get_all() -> dict[str, Any]`

Return a shallow copy of the schema dictionary. Modifying the returned
dictionary does not change the schema.

### `name in columns -> bool`

Return whether the name is present in the schema.

### `len(columns) -> int`

Return the number of columns.

### `repr(columns) -> str`

Return a debugging representation of the schema.

## `Rows`

Manage rows according to a `Columns` instance. `Table` constructs this
class with shared row storage.

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

All entries are combined with AND. Condition values are not validated
against the declared column types; comparisons follow Python semantics and
may raise `TypeError` for incompatible operands. A dictionary condition is
always treated as an operator specification, so compare a column against a
dictionary value with `{"==": value}`.

**Raises** for any condition dictionary: `ValueError` if it is not a
non-empty dictionary, names a column that does not exist, or uses an
unknown operator.

### `Rows.insert(row) -> None`

Validate and append a shallow copy of `row`.

**Arguments**

- `row`: dictionary containing exactly the schema keys and values
  compatible with their declared types.

**Raises**

- `TypeError`: `row` is not a dictionary, or a value does not match its
  type.
- `ValueError`: keys are missing or undeclared.

The copy is shallow; mutable values may remain shared.

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

- Number of deleted rows, possibly zero.

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
  values. Each value is checked against its declared type.

**Returns**

- Number of updated rows, possibly zero.

**Raises**

- `ValueError`: either argument is empty or is not a dictionary, or a
  non-existent column or filter operator is named.
- `TypeError`: a new value does not match its column type.

Arguments are validated and matches are determined before any changes are
applied. Conditions are not compared type-strictly.

### `Rows.filter(where) -> list[dict[str, Any]]`

Return shallow copies of the rows that match `where` (see
[filter conditions](#filter-conditions)), in storage order.

**Arguments**

- `where`: non-empty dictionary mapping column names to conditions.

**Returns**

- New list of shallow row copies; empty when nothing matches.

**Raises**

- `ValueError`: `where` is not a non-empty dictionary, names a non-existent
  column, or uses an unknown operator.

### `Rows.clear() -> None`

Remove all rows while preserving the schema.

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

- New dictionary of column names to new lists of values. Values are not
  copied.

**Raises:** `ValueError` if a requested name does not exist.

### `Rows.get_column(column) -> list[Any]`

Return a new list containing all values from one column. Values are not
copied.

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

Its use is optional; RAMTable invokes it when validating columns, rows,
and assigned values.

### `TypeValidator.is_supported_type(value_type) -> bool`

Return whether RAMTable can evaluate the annotation form. This does not
validate a particular value or run validators embedded in `Annotated`
metadata.

**Arguments**

- `value_type`: class or annotation to check.

**Returns**

- `True` if the annotation form is supported, otherwise `False`.

### `TypeValidator.matches_type(value, value_type) -> bool`

Check whether a value matches a supported annotation. Parameterized
containers are checked recursively. Simple classes use `isinstance`;
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

These methods are implementation details and are not part of the stable
API:

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

## Copying behavior

The schema and returned row dictionaries are shallow copies. The lists and
dictionaries returned by `get_columns` and `get_column` are new, but their
items are not copied. The exception is `Columns.add` when rows already
exist: it deep-copies the default value for each record.
