# Filter rows

The examples on this page start from a small `inventory` table:

```python exec="on" session="filter" source="above"
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

`filter(where)` returns copies of the rows that satisfy every condition in
`where`. A plain value means equality:

```python exec="on" session="filter" source="above" result="text"
in_stock = inventory.rows.filter({"active": True})
print(in_stock)
```

For anything beyond equality, map the column to a dictionary of operators:

```python exec="on" session="filter" source="above" result="text"
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

Use a callable when an operator is not enough. It receives the cell value
and must return a truthy result:

```python exec="on" session="filter" source="above" result="text"
three_char_codes = inventory.rows.filter(
    {"code": lambda code: len(code) <= 3}
)
print([row["code"] for row in three_char_codes])
```

Because a dictionary condition is always treated as an operator
specification, compare a column that stores dictionaries with the `==`
operator: `{"metadata": {"==": {"origin": "import"}}}`.

Next: [update and delete rows](updating-deleting.md).
