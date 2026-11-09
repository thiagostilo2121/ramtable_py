# User guide

This guide explains how to model temporary data with RAMTable, how to work
with records, and what to expect from validation and copying.

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

Column names must be non-empty strings; strings containing only whitespace
are rejected. Dictionary insertion order determines the order in which the
schema is returned.

The table exposes two coordinated views:

- `inventory.columns` manages the schema.
- `inventory.rows` manages the data.

Both share the same storage. Adding or removing a column updates existing
records according to the rules of that operation.

## 2. Insert rows

Each row is a dictionary containing all and only the declared columns. Values
are checked before insertion:

```python
inventory.rows.insert(
    {
        "code": "A-10",
        "description": "Notebook",
        "quantity": 12,
        "active": True,
    }
)
```

- A missing or undeclared column raises `ValueError`.
- A value that does not match its declared type raises `TypeError`.
- The table stores a shallow copy of the supplied dictionary.
- Values are not required to be unique, and no column is automatically treated
  as a primary key.

The schema is checked when a row is inserted. Simple class annotations use
`isinstance`, with the consequences described in
[types and validation](types-and-validation.md).

## 3. Read rows and columns

```python
first = inventory.rows.get_one(0)
all_rows = inventory.rows.get_all()
selected = inventory.rows.get(0, -1)
```

Calling `get()` without arguments is equivalent to retrieving all rows.
Passing one or more arguments retrieves the rows at those indexes and
preserves the requested order, including duplicates. Negative indexes work
as they do for Python lists. Boolean indexes are rejected, and an out-of-range
index raises `IndexError`.

To retrieve columns:

```python
quantities = inventory.rows.get_column("quantity")
projection = inventory.rows.get_columns("code", "quantity")
complete_table = inventory.rows.get_columns()
```

`get_column(name)` returns a list of values. `get_columns(*names)` returns a
dictionary of lists and includes every column when called without names.
Requesting a non-existent column raises `ValueError`.

Rows can also be iterated directly:

```python
for row in inventory.rows:
    print(row["code"], row["quantity"])
```

Iteration yields shallow copies of the rows, not views of the original row
dictionaries.

## 4. Update rows

`update(where, values)` applies all assignments to every row that satisfies
all equality conditions:

```python
updated_count = inventory.rows.update(
    where={"code": "A-10"},
    values={"quantity": 10, "active": False},
)
```

- `where` and `values` must be non-empty dictionaries.
- Every column name must exist in the schema.
- Values in `values` are validated against the declared type for each column.
- Conditions use `==`; their values are not validated against the column type.
- Every matching row is updated, and the return value is the number of
  modified rows (zero if there are no matches).
- The full request is validated before records are changed, avoiding partial
  updates due to an invalid column or value.

A condition such as `{"quantity": True}` may match `1`, because in Python
`True == 1`. If your application needs strict type-sensitive equality,
inspect results explicitly.

## 5. Remove rows and clear data

`remove(row)` validates the row's structure and types, then removes the first
equal row. If no such row exists, it raises `ValueError`. This version does
not provide deletion by index or condition.

To remove all records:

```python
inventory.rows.clear()
```

You can also call `inventory.clear()`. Both methods preserve all columns and
their types. `len(inventory)` and `len(inventory.rows)` return the number of
records.

## 6. Change the schema

Add a column:

```python
inventory.columns.add("location", str)
```

If the table already has rows, a default value is required:

```python
inventory.columns.add("location", str, default="warehouse")
```

RAMTable validates the default and creates an independent deep copy for each
row. If the table has no rows, a default is optional but is not stored;
future rows must provide the column as usual.

Remove a column:

```python
inventory.columns.remove("active")
```

The column is removed from the schema and every existing row. The last column
cannot be removed.

Change a column's declared type:

```python
inventory.columns.update("quantity", float)
```

This method does not convert data. The change succeeds only if every existing
value already matches the new type. Otherwise, it raises `TypeError` and
keeps the previous type.

## 7. Inspect the schema

```python
column_type = inventory.columns.get("quantity")
schema = inventory.columns.get_all()

assert "code" in inventory.columns
column_count = len(inventory.columns)
```

`get_all()` returns a new dictionary; adding or removing keys from that
dictionary does not change the table's schema. Use `add`, `remove`, and
`update` to change the schema.

## 8. Copies and mutable objects

RAMTable copies row dictionaries, but it does not deep-copy every value:

```python
row = {"id": 1, "tags": ["new"]}
```

After inserting or retrieving this row, the dictionary is independent, but
the `tags` list may still be shared. Mutating the list through either
reference may be visible through the other. Keep this in mind when storing
lists, dictionaries, or other mutable objects in cells.

The exception is a default value used to add a column to a table with rows:
RAMTable makes a deep copy of that value for each row.

## 9. Common errors

| Exception | Common cases |
|---|---|
| `ValueError` | Invalid name, non-existent column, row with missing/extra columns, empty update arguments, or row not found during removal. |
| `TypeError` | Unsupported annotation, non-dictionary row, incompatible cell value, or non-integer index (including `bool`). |
| `IndexError` | Row index out of range. |

Errors are standard Python exceptions. See the [API reference](api.md) for
method-specific arguments and exceptions.

## 10. Scope and limitations

RAMTable is a local in-memory container, not a database engine:

- it does not persist data between runs;
- it does not provide SQL, advanced filters, indexes, or uniqueness
  constraints;
- it does not implement transactions, concurrent storage, or synchronization
  across processes;
- it is not a replacement for a database when durability, complex queries, or
  coordination between multiple users are required.

Use RAMTable when the data lifetime matches the program's execution and its
schema and row operations provide enough structure.
