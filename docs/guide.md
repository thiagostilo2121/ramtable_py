# User guide

This guide explains how to model temporary data with RAMTable: creating
tables, working with rows, evolving the schema, and reading data back out.

The snippets build on one example: an `inventory` table created in
section 1 and populated in section 2. Each later section stands alone
unless stated otherwise. For exact signatures and the exceptions raised by
each method, see the [API reference](api.md).

## Contents

1. [Create a table](#1-create-a-table)
2. [Insert rows](#2-insert-rows)
3. [Read rows and columns](#3-read-rows-and-columns)
4. [Update rows](#4-update-rows)
5. [Remove rows and clear data](#5-remove-rows-and-clear-data)
6. [Change the schema](#6-change-the-schema)
7. [Inspect the schema](#7-inspect-the-schema)
8. [Copies and mutable values](#8-copies-and-mutable-values)
9. [Errors reference](#9-errors-reference)
10. [Scope and limitations](#10-scope-and-limitations)

## 1. Create a table

A table requires a non-empty name and a schema with at least one column. The
schema is a dictionary mapping each column name to a supported class or type
annotation:

```python
from ramtable import Table

inventory = Table(
    name="inventory",
    columns={
        "code": str,
        "description": str,
        "quantity": int,
        "active": bool,
    },
)
```

Column names must be non-empty strings; names containing only whitespace are
rejected. The dictionary's insertion order determines the order in which the
schema is reported.

Every table exposes two views over one shared storage:

```text
inventory
├── columns → Columns   the schema: column names and declared types
└── rows    → Rows      the data: insert, read, update, remove
```

Because both views share the same storage, schema changes are applied to
existing rows, and row operations always validate against the current
schema.

## 2. Insert rows

Each row is a dictionary containing all and only the declared columns.
Values are checked before insertion:

```python
inventory.rows.insert(
    {
        "code": "A-10",
        "description": "Notebook",
        "quantity": 12,
        "active": True,
    }
)

inventory.rows.insert(
    {
        "code": "B-2",
        "description": "Mechanical pencil",
        "quantity": 3,
        "active": False,
    }
)
```

- A row missing columns, or containing undeclared ones, raises `ValueError`.
- A value that does not match its column's declared type raises `TypeError`.
- The table stores a shallow copy of the dictionary you pass in.
- Values are not required to be unique, and no column is automatically
  treated as a primary key.

Validation follows the rules described in
[types and validation](types-and-validation.md).

## 3. Read rows and columns

Read rows by position:

```python
first = inventory.rows.get_one(0)
# {'code': 'A-10', 'description': 'Notebook', 'quantity': 12, 'active': True}

last = inventory.rows.get_one(-1)      # negative indexes, as in lists
first_and_last = inventory.rows.get(0, -1)
every_row = inventory.rows.get()       # no arguments: all rows
```

- `get()` without arguments is equivalent to retrieving all rows.
- With indexes, `get()` returns the rows at those positions, preserving the
  requested order; repeats are allowed.
- Negative indexes behave as they do for Python lists.
- Boolean indexes are rejected, and an out-of-range index raises
  `IndexError`.

Read columns as lists:

```python
quantities = inventory.rows.get_column("quantity")
# [12, 3]

pairs = inventory.rows.get_columns("code", "quantity")
# {'code': ['A-10', 'B-2'], 'quantity': [12, 3]}

everything = inventory.rows.get_columns()  # every column in the schema
```

- `get_column(name)` returns a list with the values of one column.
- `get_columns(*names)` returns a dictionary of lists; without arguments it
  includes every column.
- Requesting a column that does not exist raises `ValueError`.

Rows can also be iterated directly:

```python
for row in inventory.rows:
    print(row["code"], row["quantity"])
# A-10 12
# B-2 3
```

Iteration yields shallow copies of the rows, not views of the stored
dictionaries.

## 4. Update rows

`update(where, values)` applies all assignments in `values` to every row
that satisfies all the equality conditions in `where`:

```python
updated_count = inventory.rows.update(
    where={"code": "A-10"},
    values={"quantity": 10, "active": False},
)
# 1
```

- `where` and `values` must be non-empty dictionaries naming existing
  columns.
- Each value in `values` is validated against its column's declared type.
- Values in `where` are compared with `==` and are not validated against the
  column type.
- The return value is the number of updated rows, which is zero when
  nothing matches.
- The whole request is validated before any row is modified, so an invalid
  request never leaves a partial change behind.

> [!NOTE]
> Because conditions use `==`, a condition such as `{"quantity": True}`
> matches a row whose quantity is `1`, following Python's rule that
> `True == 1`. Inspect results explicitly if you need type-sensitive
> equality.

## 5. Remove rows and clear data

`remove(row)` validates the row's structure and types, then removes the
first row equal to it:

```python
inventory.rows.remove(
    {
        "code": "B-2",
        "description": "Mechanical pencil",
        "quantity": 3,
        "active": False,
    }
)
```

If no equal row exists, the method raises `ValueError`.

> [!NOTE]
> This version does not provide deletion by index or by condition. Rows are
> removed by their full content.

To remove all records:

```python
inventory.rows.clear()
# or, equivalently:
inventory.clear()
```

Both methods preserve all columns and their types. `len(inventory)` and
`len(inventory.rows)` return the current number of rows.

## 6. Change the schema

Add a column to a table without rows:

```python
inventory.columns.add("location", str)
```

If the table already has rows, a default value is required:

```python
inventory.columns.add("location", str, default="warehouse")
```

The default is validated against the column's type and deep-copied
independently for every row, so mutable defaults are never shared. When the
table has no rows, the default is optional and is not stored; future rows
must supply the column as usual.

Remove a column:

```python
inventory.columns.remove("active")
```

The column disappears from the schema and from every existing row. The last
remaining column cannot be removed: a table always keeps at least one
column.

Change a column's declared type:

```python
inventory.columns.update("quantity", float)
```

Retyping never converts stored values. The change is applied only when every
existing value already matches the new annotation; otherwise the method
raises `TypeError` and the column keeps its previous type. With integers
stored in `quantity`, the call above fails; convert the data yourself first
if you need a real type change.

## 7. Inspect the schema

```python
inventory.columns.get("quantity")    # int
schema = inventory.columns.get_all()  # new dict: column name → annotation

"code" in inventory.columns           # True
len(inventory.columns)                # 4
```

`get_all()` returns a new dictionary, so modifying it has no effect on the
table. Use `add`, `remove`, and `update` to change the schema.

## 8. Copies and mutable values

RAMTable copies row dictionaries, but it does not deep-copy every value:

```python
row = {"id": 1, "tags": ["new"]}
```

After inserting this row, or after reading a row back, the dictionary you
hold is independent of the stored one, but the `tags` list is the same
object in both. Mutating it through either reference is visible through the
other. Keep this in mind when storing lists, dictionaries, or other
mutable values in cells.

The exception is a default passed to `columns.add()` when rows already
exist: RAMTable deep-copies that value once per row.

## 9. Errors reference

| Exception | Raised for |
|---|---|
| `ValueError` | Invalid table or column name, empty schema, non-existent column, row with missing or extra columns, empty update arguments, or row not found during removal. |
| `TypeError` | Unsupported annotation, non-dictionary row, value that does not match its column type, or non-integer index (including `bool`). |
| `IndexError` | Row index out of range. |

Errors are standard Python exceptions with descriptive messages. See the
[API reference](api.md) for the exceptions raised by each method.

## 10. Scope and limitations

RAMTable is a local in-memory container, not a database engine:

- it does not persist data between runs;
- it provides no SQL, advanced filters, indexes, or uniqueness constraints;
- it implements no transactions, no concurrent storage, and no
  synchronization across processes;
- it is not a replacement for a database when durability, complex queries,
  or coordination between multiple users are required.

Use RAMTable when the data's lifetime matches the program's execution, and
when its schema and row operations provide enough structure for the task.
