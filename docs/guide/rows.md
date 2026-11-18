# Insert and read rows

The examples on this page use one `inventory` table:

```python exec="on" session="rows" source="above"
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

## Insert rows

A row is a dictionary with the declared columns, except those with an insert
default. RAMTable checks values before insertion:

```python exec="on" session="rows" source="above" result="text"
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
  a deep copy of the default. [Create a table](create-table.md) shows how to
  declare one.
- A row missing a column without a default, or containing undeclared ones,
  raises `ValueError`.
- A value that does not match its column's declared type raises `TypeError`.
  An explicit value is never replaced by a default, even if it is `None`.
- The table stores a shallow copy of the dictionary you pass in.
- Values need not be unique, and no column acts as a primary key.

To insert several rows with one call, use `insert_many()`:

```python exec="on" session="rows" source="above" result="text"
restock = Table("restock", {"code": str, "quantity": int})

inserted = restock.rows.insert_many(
    [
        {"code": "E-5", "quantity": 8},
        {"code": "F-6", "quantity": 2},
    ]
)
print(inserted)
```

`insert_many()` accepts any iterable of dictionaries and returns how many
rows it inserted. It validates every row before storing any of them, so a
bad row leaves the table unchanged. Insert defaults apply to each row, with
a separate deep copy per row.

Validation follows the rules described in
[types and validation](../reference/types-and-validation.md).

## Read rows and columns

Read rows by position:

```python exec="on" session="rows" source="above" result="text"
first = inventory.rows.get_one(0)
last = inventory.rows.get_one(-1)
first_and_last = inventory.rows.get(0, -1)
every_row = inventory.rows.get()
every_row = inventory.rows.get_all()

print(first)
print(last["code"])
print(len(first_and_last), len(every_row))
```

- `get()` without arguments returns every row; `get_all()` is its alias.
- With indexes, `get()` returns the rows at those positions, preserving the
  requested order; repeats are allowed.
- Negative indexes behave as they do for Python lists.
- RAMTable rejects boolean indexes; an out-of-range index raises
  `IndexError`.

Read columns as lists:

```python exec="on" session="rows" source="above" result="text"
quantities = inventory.rows.get_column("quantity")
pairs = inventory.rows.get_columns("code", "quantity")
everything = inventory.rows.get_columns()

print(quantities)
print(pairs)
print(sorted(everything))
```

- `get_column(name)` returns a list with the values of one column.
- `get_columns(*names)` returns a dictionary of lists; without arguments it
  includes every column.
- Requesting a column that does not exist raises `ValueError`.

Rows can also be iterated directly:

```python exec="on" session="rows" source="above" result="text"
for row in inventory.rows:
    print(row["code"], row["quantity"])
```

Iteration yields shallow copies of the rows, not views of the stored
dictionaries.

## Copies and mutable values

RAMTable copies row dictionaries; cell values keep their identity:

```python exec="on" session="rows" source="above" result="text"
notes = Table("notes", {"id": int, "tags": list[str]})

row = {"id": 1, "tags": ["new"]}
notes.rows.insert(row)

row["tags"].append("changed")
print(notes.rows.get_one(0)["tags"])
```

After you insert or read a row, your dictionary is independent of the stored
one, but both point to the same `tags` list. A mutation through either
reference shows up in both. Watch this when you store lists, dictionaries,
or other mutable values in cells.

RAMTable deep-copies a `fill_value` passed to `columns.add()` when rows
exist, once per row. It also deep-copies an insert default when you set it,
each time a row omits the column, and when `get_default()` or
`get_defaults()` returns it.

Next: [filter rows](filtering.md).
