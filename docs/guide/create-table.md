# Create a table

RAMTable requires a non-empty name and a schema with at least one column.
The schema is a dictionary mapping each column name to a supported class or
type annotation:

```python exec="on" session="create" source="above"
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

```python exec="on" session="create" source="above" result="text"
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
`columns.remove_default()`, and `columns.get_defaults()`; see
[change the schema](schema.md).

Each table exposes two views of the same storage:

```text
inventory
├── columns → Columns   the schema: column names and declared types
└── rows    → Rows      the data: insert, read, filter, update, remove
```

Schema changes reach the existing rows, and row operations validate against
the current schema.

Next: [insert and read rows](rows.md).
