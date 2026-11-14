# API reference

This reference documents each public symbol: `Table`, `Columns`, `Rows`,
`TypeValidator`, and the package version. The class pages are generated from
the package docstrings. The [user guide](../guide/index.md) introduces the
same API with examples.

```python
from ramtable import Columns, Rows, Table, __version__
from ramtable.types import TypeValidator
```

You normally create only a `Table`; it builds the matching `Columns` and
`Rows` and exposes them as `table.columns` and `table.rows`.

## Class reference

- [`Table`](api/table.md): named in-memory table with a typed schema and
  rows.
- [`Columns`](api/columns.md): schema operations, including add, remove,
  update, and insert defaults.
- [`Rows`](api/rows.md): row operations, filter conditions, and retrieval
  methods.
- [`TypeValidator`](api/types.md): runtime checks for supported annotations
  and values.

`Table` coordinates `Columns` and `Rows` and shares one record store between
them. Data lives only in memory.

## Package version

```python
from ramtable import __version__
```

`__version__` is the version of the installed distribution, read from its
package metadata. It matches `project.version` in `pyproject.toml` and the
artifact built from it. In a source checkout that has not been installed,
it is `"0+unknown"`.

## Internal helpers

Implementation details outside the stable API. They are not part of the
generated class pages:

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
