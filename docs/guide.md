# User guide

This guide explains how to model temporary data with RAMTable: creating
tables, working with rows, filtering, evolving the schema, and reading
data back out.

The snippets build on one example: an `inventory` table created in
section 1 and populated in section 2. Each later section stands alone
unless stated otherwise. For exact signatures and the exceptions raised by
each method, see the [API reference](api.md).

## Contents

1. [Create a table](#1-create-a-table)
2. [Insert rows](#2-insert-rows)
3. [Read rows and columns](#3-read-rows-and-columns)
4. [Filter rows](#4-filter-rows)
5. [Update rows](#5-update-rows)
6. [Remove and delete rows](#6-remove-and-delete-rows)
7. [Change the schema](#7-change-the-schema)
8. [Inspect the schema](#8-inspect-the-schema)
9. [Copies and mutable values](#9-copies-and-mutable-values)
10. [Errors reference](#10-errors-reference)
11. [Scope and limitations](#11-scope-and-limitations)

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

An optional `defaults` mapping declares values for columns that may be
omitted when inserting rows:

```python
inventory = Table(
    name="inventory",
    columns={
        "code": str,
        "quantity": int,
        "active": bool,
    },
    defaults={"quantity": 0, "active": True},
)
```

Each default is validated against its column type when the table is created.
Defaults never replace values supplied explicitly by a row. They must also
support `copy.deepcopy`; if a value cannot be copied, table creation raises
`TypeError` with the offending column name.

Every table exposes two views over one shared storage:

```text
inventory
├── columns → Columns   the schema: column names and declared types
└── rows    → Rows      the data: insert, read, filter, update, remove
```

Because both views share the same storage, schema changes are applied to
existing rows, and row operations always validate against the current
schema.

## 2. Insert rows

Each row is a dictionary containing the declared columns, except those with
an insert default. Values are checked before insertion:

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

- A row may omit a column that has an insert default; RAMTable fills it with
  a deep copy of the default.
- A row missing a column without a default, or containing undeclared ones,
  raises `ValueError`.
- A value that does not match its column's declared type raises `TypeError`.
  An explicit value is never replaced by a default, even if it is `None`.
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

## 4. Filter rows

`filter(where)` returns copies of the rows that satisfy every condition in
`where`. A plain value means equality:

```python
in_stock = inventory.rows.filter({"active": True})
# [{'code': 'A-10', ...}]
```

For anything beyond equality, map the column to a dictionary of operators:

```python
low_stock = inventory.rows.filter({"quantity": {"<": 5}})

notebooks = inventory.rows.filter(
    {"description": {"contains": "book"}}
)

short_codes = inventory.rows.filter(
    {"code": {"startswith": "A"}, "active": {"==": True}}
)
```

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

- Conditions are combined with AND: every entry in `where` and every
  operator for a column must match.
- Several operators for the same column are allowed:
  `{"quantity": {">=": 1, "<": 5}}`.
- `filter()` returns rows in storage order, always in a new list, even when
  nothing matches.
- Condition values are not validated against the declared column types;
  comparisons follow Python semantics, so incompatible operands raise the
  usual `TypeError`.

A callable can be used when an operator is not enough. It receives the cell
value and must return a truthy result:

```python
short_codes = inventory.rows.filter(
    {"code": lambda code: len(code) <= 3}
)
```

Because a dictionary condition is always treated as an operator
specification, compare a column that stores dictionaries with the `==`
operator: `{"metadata": {"==": {"origin": "import"}}}`.

## 5. Update rows

`update(where, values)` applies all assignments in `values` to every row
that satisfies `where`. Conditions use the same format as `filter()`:

```python
updated_count = inventory.rows.update(
    where={"code": "A-10"},
    values={"quantity": 10, "active": False},
)
# 1
```

Conditions can be expressions, not only equality:

```python
inventory.rows.update(
    where={"code": {"startswith": "B"}},
    values={"active": True},
)
# 1
```

- `where` and `values` must be non-empty dictionaries naming existing
  columns.
- Each value in `values` is validated against its column's declared type.
- Condition values are compared directly and are not validated against the
  column type.
- The return value is the number of updated rows, which is zero when
  nothing matches.
- The whole request is validated before any row is modified, so an invalid
  request never leaves a partial change behind.

> [!NOTE]
> Because the `==` operator follows Python equality, a condition such as
> `{"quantity": True}` matches a row whose quantity is `1`, following the
> rule that `True == 1`. Inspect results explicitly if you need
> type-sensitive equality.

## 6. Remove and delete rows

To remove one specific row by its full content, use `remove(row)`:

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

`remove()` validates the row's structure and types, then removes the first
equal row. If no equal row exists, it raises `ValueError`.

To remove every row that matches a condition, use `delete(where)`:

```python
deleted_count = inventory.rows.delete(
    {"code": {"startswith": "A"}}
)
# 1
```

`delete()` accepts the same conditions as `filter()` and `update()`,
removes all matching rows, and returns how many were deleted (zero when
nothing matches).

> [!NOTE]
> `remove()` targets a single row by its full content; `delete()` targets
> every row that matches a condition.

To remove all records:

```python
inventory.rows.clear()
# or, equivalently:
inventory.clear()
```

Both methods preserve all columns and their types. `len(inventory)` and
`len(inventory.rows)` return the current number of rows.

## 7. Change the schema

Add a column to a table without rows:

```python
inventory.columns.add("location", str)
```

If the table already has rows, a fill value is required:

```python
inventory.columns.add("location", str, fill_value="warehouse")
```

The fill value is validated against the column's type and deep-copied
independently for every row, so mutable values are never shared. When the
table has no rows, the fill value is optional and is not stored; it does not
become an insert default. A column added after the table is created can only
be omitted from inserts if it already has an insert default, which is not the
case for columns added with `columns.add()`.

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
existing value already matches the new annotation and the column's insert
default, if any, also matches; otherwise the method raises `TypeError` and
the column keeps its previous type. With integers
stored in `quantity`, the call above fails; convert the data yourself first
if you need a real type change.

## 8. Inspect the schema

```python
inventory.columns.get("quantity")     # int
schema = inventory.columns.get_all()  # new dict: column name → annotation

"code" in inventory.columns           # True
len(inventory.columns)                # 4
```

`get_all()` returns a new dictionary, so modifying it has no effect on the
table. Use `add`, `remove`, and `update` to change the schema.

Read an insert default with `get_default()`:

```python
inventory.columns.get_default("active")  # True
```

The method returns a deep copy, so mutating it does not change the stored
default. It raises `ValueError` when the column does not exist or has no
insert default. Removing a column also removes its insert default.

## 9. Copies and mutable values

RAMTable copies row dictionaries, but it does not deep-copy every value:

```python
row = {"id": 1, "tags": ["new"]}
```

After inserting this row, or after reading a row back, the dictionary you
hold is independent of the stored one, but the `tags` list is the same
object in both. Mutating it through either reference is visible through the
other. Keep this in mind when storing lists, dictionaries, or other
mutable values in cells.

Two exceptions apply. A fill value passed to `columns.add()` when rows
already exist is deep-copied once per row. Likewise, an insert default is
deep-copied when the table is created, whenever a row omits that column, and
when it is returned by `columns.get_default()`.

## 10. Errors reference

| Exception | Raised for |
|---|---|
| `ValueError` | Invalid table or column name, empty schema, non-existent column, a default for an unknown column, row with missing or extra columns, empty update or filter arguments, unknown filter operator, or row not found during removal. |
| `TypeError` | Unsupported annotation, non-dictionary defaults or row, value or default that does not match its column type, a default that cannot be deep-copied, non-integer index (including `bool`), or an incompatible filter operand. |
| `IndexError` | Row index out of range. |

Errors are standard Python exceptions with descriptive messages. See the
[API reference](api.md) for the exceptions raised by each method.

## 11. Scope and limitations

RAMTable is a local in-memory container, not a database engine:

- it does not persist data between runs;
- it provides no SQL, indexes, or uniqueness constraints; filters cover
  common comparisons, membership, and string matching, but not joins or
  aggregation;
- it implements no transactions, no concurrent storage, and no
  synchronization across processes;
- it is not a replacement for a database when durability, complex queries,
  or coordination between multiple users are required.

Use RAMTable when the data's lifetime matches the program's execution, and
when its schema and row operations provide enough structure for the task.
