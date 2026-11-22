# Update and delete rows

The examples on this page start from a small `inventory` table:

```python exec="on" session="update" source="above"
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

inventory.rows.insert_many(
    [
        {
            "code": "A-10",
            "description": "Notebook",
            "quantity": 12,
            "active": True,
        },
        {
            "code": "B-2",
            "description": "Mechanical pencil",
            "quantity": 3,
            "active": False,
        },
        {
            "code": "C-7",
            "description": "Notebook cover",
            "quantity": 1,
            "active": True,
        },
    ]
)
```

## Update rows

`update(where, values)` applies all assignments in `values` to every row
that satisfies `where`. Conditions use the same format as
[`filter()`](filtering.md):

```python exec="on" session="update" source="above" result="text"
updated_count = inventory.rows.update(
    where={"code": "A-10"},
    values={"quantity": 10, "active": False},
)
print(updated_count)
```

Conditions accept expressions too:

```python exec="on" session="update" source="above" result="text"
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

## Delete rows

To remove one specific row by its full content, use `remove(row)`:

```python exec="on" session="update" source="above" result="text"
inventory.rows.remove(
    {
        "code": "B-2",
        "description": "Mechanical pencil",
        "quantity": 3,
        "active": True,
    }
)
print([row["code"] for row in inventory.rows])
```

`remove()` validates the row's structure and types, then removes the first
equal row. If no equal row exists, it raises `ValueError`. The example
passes `active` as `True` because the update above set it.

To remove every row that matches a condition, use `delete(where)`:

```python exec="on" session="update" source="above" result="text"
deleted_count = inventory.rows.delete(
    {"code": {"startswith": "A"}}
)
print(deleted_count)
```

`delete()` accepts the same conditions as `filter()` and `update()`,
removes all matching rows, and returns how many were deleted (zero when
nothing matches).

> [!NOTE]
> `remove()` targets a single row by its full content; `delete()` targets
> every row that matches a condition.

To remove a row by position, use `pop(index)`:

```python exec="on" session="update" source="above" result="text"
queue = Table("queue", {"id": int})
queue.rows.insert_many([{"id": 1}, {"id": 2}])

removed = queue.rows.pop(-1)
print(removed, len(queue.rows))
```

`pop()` accepts negative indexes and returns the removed row as a shallow
copy. It rejects boolean indexes, and an out-of-range index raises
`IndexError`.

To remove all records:

```python
inventory.rows.clear()
# or, equivalently:
inventory.clear()
```

Both methods preserve all columns, their types, and their insert defaults.
`len(inventory)` and `len(inventory.rows)` return the current number of
rows.

Next: [change the schema](schema.md).
