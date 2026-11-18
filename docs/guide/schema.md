# Change the schema

Schema changes act on the same storage as row operations, so every change
must account for the rows already in the table.

## Add a column

On an empty table, add a column without a fill value:

```python exec="on" session="schema" source="above" result="text"
from ramtable import Table

catalog = Table("catalog", {"code": str})
catalog.columns.add("location", str)
print(catalog.columns.get_all())
```

When rows exist, pass a fill value:

```python exec="on" session="schema" source="above" result="text"
stock = Table("stock", {"code": str, "quantity": int})
stock.rows.insert({"code": "A-10", "quantity": 12})

stock.columns.add("location", str, fill_value="warehouse")
print(stock.rows.get_one(0))
```

RAMTable validates the fill value and deep-copies it for each row, so rows
never share a mutable value. On an empty table the fill value is optional
and RAMTable does not store it.

An insert default is independent of the fill value:

```python exec="on" session="schema" source="above" result="text"
orders = Table("orders", {"code": str, "quantity": int})
orders.rows.insert({"code": "A-10", "quantity": 12})

orders.columns.add(
    "status",
    str,
    fill_value="archived",
    default="available",
)

print(orders.rows.get_one(0)["status"])
orders.rows.insert({"code": "B-2", "quantity": 4})
print(orders.rows.get_one(1)["status"])
```

Providing `default` does not remove the fill-value requirement. If `orders`
had rows and you called `columns.add("priority", int, default=1)`, RAMTable
would raise `ValueError`. On an empty table, `default` is stored even though
no rows need a fill value.

Manage defaults after creation:

```python exec="on" session="schema" source="above" result="text"
orders.columns.set_default("status", "pending")
print(orders.columns.get_default("status"))
print(orders.columns.get_defaults())

orders.columns.remove_default("status")
```

`set_default()` validates the value against the column type and replaces any
existing default. `remove_default()` makes future inserts require the column
again. `get_defaults()` returns deep copies of every default.

## Remove a column

```python exec="on" session="schema" source="above" result="text"
catalog.columns.remove("location")
print(catalog.columns.get_all())
```

The column, its values, and its insert default disappear. You cannot remove
the last remaining column; a table always keeps at least one.

## Change a column type

```python
stock.columns.update("quantity", float)
```

Retyping never converts stored values. RAMTable changes the schema only when
every existing value and the insert default, if any, already match the new
annotation. Otherwise it raises `TypeError` and keeps the old type. The
integer stored in `stock.quantity` fails this check; convert the data
yourself first.

## Inspect the schema

```python exec="on" session="schema" source="above" result="text"
settings = Table(
    "settings",
    {"theme": str, "active": bool},
    defaults={"active": True},
)

print(settings.columns.get("theme"))
print(settings.columns.get_all())
print("theme" in settings.columns)
print(len(settings.columns))
```

`get_all()` returns a new dictionary, so modifying it has no effect on the
table. Use `add`, `remove`, and `update` to change the schema.

Read one insert default with `get_default()`, or every default with
`get_defaults()`:

```python exec="on" session="schema" source="above" result="text"
print(settings.columns.get_default("active"))
print(settings.columns.get_defaults())
```

Both methods return deep copies, so mutating the result leaves the stored
defaults intact. `get_default()` raises `ValueError` when the column does
not exist or has no insert default. Removing a column removes its default
too.
