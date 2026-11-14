# User guide

RAMTable holds temporary data in typed tables. This guide covers creating
them, inserting and reading rows, filtering, and changing the schema.

Most examples use one `inventory` table, created in section 1 and populated
in section 2. Section 1 also defines a separate `tasks` table for insert
defaults. Later sections stand alone unless noted. For exact signatures and
exceptions, see the [API reference](../reference/index.md).

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

RAMTable requires a non-empty name and a schema with at least one column.
The schema is a dictionary mapping each column name to a supported class or
type annotation:

```python exec="on" session="guide" source="above"
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

Column names must be non-empty strings with at least one non-whitespace
character. The schema keeps the dictionary order.

The optional `defaults` mapping gives values to columns that rows may omit:

```python exec="on" session="guide" source="above" result="text"
tasks = Table(
    name="tasks",
    columns={
        "title": str,
        "status": str,
        "retries": int,
    },
    defaults={"status": "pending", "retries": 0},
)

tasks.rows.insert({"title": "write docs"})
print(tasks.rows.get_one(0))
```

RAMTable validates each default when it creates the table and stores a deep
copy. An explicit value in a row always wins. A default that cannot be
deep-copied raises `TypeError` with the column name. You can also manage
defaults after creation with `columns.set_default()`,
`columns.remove_default()`, and `columns.get_defaults()`.

Each table exposes two views of the same storage:

```text
inventory
├── columns → Columns   the schema: column names and declared types
└── rows    → Rows      the data: insert, read, filter, update, remove
```

Schema changes reach the existing rows, and row operations validate against
the current schema.

## 2. Insert rows

A row is a dictionary with the declared columns, except those with an insert
default. RAMTable checks values before insertion:

```python exec="on" session="guide" source="above"
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

print(len(inventory.rows))
```

- A row may omit a column that has an insert default; RAMTable fills it with
  a deep copy of the default.
- A row missing a column without a default, or containing undeclared ones,
  raises `ValueError`.
- A value that does not match its column's declared type raises `TypeError`.
  An explicit value is never replaced by a default, even if it is `None`.
- The table stores a shallow copy of the dictionary you pass in.
- Values need not be unique, and no column acts as a primary key.

Validation follows the rules described in
[types and validation](../reference/types-and-validation.md).

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
- RAMTable rejects boolean indexes; an out-of-range index raises
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

```python exec="on" session="guide" source="above" result="text"
in_stock = inventory.rows.filter({"active": True})
print(in_stock)
```

For anything beyond equality, map the column to a dictionary of operators:

```python exec="on" session="guide" source="above" result="text"
low_stock = inventory.rows.filter({"quantity": {"<": 5}})

notebooks = inventory.rows.filter(
    {"description": {"contains": "book"}}
)

short_codes = inventory.rows.filter(
    {"code": {"startswith": "A"}, "active": {"==": True}}
)

print([row["code"] for row in low_stock])
print([row["code"] for row in notebooks])
print([row["code"] for row in short_codes])
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

Use a callable when an operator is not enough. It receives the cell
value and must return a truthy result:

```python exec="on" session="guide" source="above" result="text"
three_char_codes = inventory.rows.filter(
    {"code": lambda code: len(code) <= 3}
)
print([row["code"] for row in three_char_codes])
```

Because a dictionary condition is always treated as an operator
specification, compare a column that stores dictionaries with the `==`
operator: `{"metadata": {"==": {"origin": "import"}}}`.

## 5. Update rows

`update(where, values)` applies all assignments in `values` to every row
that satisfies `where`. Conditions use the same format as `filter()`:

```python exec="on" session="guide" source="above" result="text"
updated_count = inventory.rows.update(
    where={"code": "A-10"},
    values={"quantity": 10, "active": False},
)
print(updated_count)
```

Conditions accept expressions too:

```python exec="on" session="guide" source="above" result="text"
updated_count = inventory.rows.update(
    where={"code": {"startswith": "B"}},
    values={"active": True},
)
print(updated_count)
```

- `where` and `values` must be non-empty dictionaries naming existing
  columns.
- RAMTable validates each value in `values` against its column's declared
  type.
- RAMTable compares condition values directly without validating them
  against the column type.
- The return value is the number of updated rows, zero when nothing
  matches.
- RAMTable validates the whole request before changing any row.

> [!NOTE]
> Because the `==` operator follows Python equality, a condition such as
> `{"quantity": True}` matches a row whose quantity is `1`, following the
> rule that `True == 1`. Inspect results explicitly if you need
> type-sensitive equality.

## 6. Remove and delete rows

This section continues from section 5, which set the `active` value of B-2
to `True`.

To remove one specific row by its full content, use `remove(row)`:

```python
inventory.rows.remove(
    {
        "code": "B-2",
        "description": "Mechanical pencil",
        "quantity": 3,
        "active": True,
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

Both methods preserve all columns, their types, and their insert defaults.
`len(inventory)` and `len(inventory.rows)` return the current number of
rows.

## 7. Change the schema

Section 6 left `inventory` empty. On an empty table, add a column without a
fill value:

```python
inventory.columns.add("location", str)
```

When rows exist, pass a fill value. This example uses a separate table:

```python
stock = Table("stock", {"code": str, "quantity": int})
stock.rows.insert({"code": "A-10", "quantity": 12})

stock.columns.add("location", str, fill_value="warehouse")
stock.rows.get_one(0)
# {'code': 'A-10', 'quantity': 12, 'location': 'warehouse'}
```

RAMTable validates the fill value and deep-copies it for each row, so rows
never share a mutable value. On an empty table the fill value is optional
and RAMTable does not store it.

An insert default is independent. This example uses its own table:

```python
orders = Table("orders", {"code": str, "quantity": int})
orders.rows.insert({"code": "A-10", "quantity": 12})

orders.columns.add(
    "status",
    str,
    fill_value="archived",
    default="available",
)

orders.rows.get_one(0)["status"]              # 'archived'
orders.rows.insert({"code": "B-2", "quantity": 4})
orders.rows.get_one(1)["status"]              # 'available'
```

Providing `default` does not remove the fill-value requirement. If `orders`
had rows and you called `columns.add("priority", int, default=1)`, RAMTable
would raise `ValueError`. On an empty table, `default` is stored even though
no rows need a fill value.

Manage defaults after creation:

```python
orders.columns.set_default("status", "pending")
orders.columns.get_default("status")   # 'pending'
orders.columns.get_defaults()          # {'status': 'pending'}

orders.columns.remove_default("status")
```

`set_default()` validates the value against the column type and replaces any
existing default. `remove_default()` makes future inserts require the column
again. `get_defaults()` returns deep copies of every default.

Remove a column:

```python
inventory.columns.remove("active")
```

The column, its values, and its insert default disappear. You cannot remove
the last remaining column; a table always keeps at least one.

Change a column's declared type:

```python
stock.columns.update("quantity", float)
```

Retyping never converts stored values. RAMTable changes the schema only when
every existing value and the insert default, if any, already match the new
annotation. Otherwise it raises `TypeError` and keeps the old type. The
integer stored in `stock.quantity` fails this check; convert the data
yourself first.

## 8. Inspect the schema

This section uses its own `settings` table:

```python
settings = Table(
    "settings",
    {"theme": str, "active": bool},
    defaults={"active": True},
)

settings.columns.get("theme")           # str
schema = settings.columns.get_all()     # new dict: column name → annotation

"theme" in settings.columns             # True
len(settings.columns)                   # 2
```

`get_all()` returns a new dictionary, so modifying it has no effect on the
table. Use `add`, `remove`, and `update` to change the schema.

Read one insert default with `get_default()`, or every default with
`get_defaults()`:

```python
settings.columns.get_default("active")   # True
settings.columns.get_defaults()           # {'active': True}
```

Both methods return deep copies, so mutating the result leaves the stored
defaults intact. `get_default()` raises `ValueError` when the column does
not exist or has no insert default. Removing a column removes its default
too.

## 9. Copies and mutable values

RAMTable copies row dictionaries; cell values keep their identity:

```python
notes = Table("notes", {"id": int, "tags": list[str]})

row = {"id": 1, "tags": ["new"]}
notes.rows.insert(row)

row["tags"].append("changed")
notes.rows.get_one(0)["tags"]
# ['new', 'changed']
```

After you insert or read a row, your dictionary is independent of the stored
one, but both point to the same `tags` list. A mutation through either
reference shows up in both. Watch this when you store lists, dictionaries,
or other mutable values in cells.

RAMTable deep-copies a `fill_value` passed to `columns.add()` when rows
exist, once per row. It also deep-copies an insert default when you set it,
each time a row omits the column, and when `get_default()` or
`get_defaults()` returns it.

## 10. Errors reference

| Exception | Raised for |
|---|---|
| `ValueError` | Invalid table or column name, empty schema, non-existent column, a default for an unknown column, row with missing or extra columns, empty update or filter arguments, unknown filter operator, or row not found during removal. |
| `TypeError` | Unsupported annotation, non-dictionary defaults or row, value or default that does not match its column type, a default that cannot be deep-copied, non-integer index (including `bool`), or an incompatible filter operand. |
| `IndexError` | Row index out of range. |

Errors are standard Python exceptions with descriptive messages. See the
[API reference](../reference/index.md) for the exceptions each method raises.

## 11. Scope and limitations

RAMTable is a local in-memory container:

- it does not persist data between runs;
- it provides no SQL, indexes, or uniqueness constraints; filters cover
  common comparisons, membership, and string matching, but not joins or
  aggregation;
- it implements no transactions, no concurrent storage, and no
  synchronization across processes;
- it is not a replacement for a database when durability, complex queries,
  or coordination between multiple users are required.

Use it when the data lives as long as the program and the schema and row
operations give you enough structure.
