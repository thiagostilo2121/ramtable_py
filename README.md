# RAMTable

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
[![PyPI](https://img.shields.io/pypi/v/ramtable)](https://pypi.org/project/ramtable/)
[![TestPyPI](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Ftest.pypi.org%2Fpypi%2Framtable%2Fjson&label=TestPyPI&query=%24.info.version&color=blue)](https://test.pypi.org/project/ramtable/)

RAMTable stores typed tables in memory for data that lives as long as the
program. You declare a schema, and the table validates every row.

The library has no runtime dependencies. Data stays in memory and disappears
when the process ends. RAMTable executes no SQL and writes nothing to disk.

## Where it fits

Use RAMTable when a plain `list` or `dict` lacks structure and a persistent
database is more than you need:

| | Plain `list` / `dict` | RAMTable | SQL database |
|---|:---:|:---:|:---:|
| Schema with declared types | No | ✓ | ✓ |
| Rows validated on write | No | ✓ | ✓ |
| Schema changes with data present | manual | ✓ | ✓ |
| Query language, indexes, constraints | No | No | ✓ |
| Survives process exit | No | No | ✓ |
| Setup | none | none | server or files |

Typical scenarios:

- intermediate results of a multi-step process;
- temporary records staged during a calculation or import;
- the working set of a long-running task;
- prototypes that want typed rows before a real database exists.

For simple collections, use a list or dictionary. If data must survive
restarts, be shared between processes, or be queried with SQL, use a
persistence layer. For analysis and vectorized operations, use a data-frame
library.

## Installation

Use Python 3.11 or later.

Install the latest stable release from PyPI:

```bash
python -m pip install ramtable
```

TestPyPI hosts pre-releases. To try one:

```bash
python -m pip install --pre --index-url https://test.pypi.org/simple/ ramtable
```

TestPyPI is a separate testing index. Stable releases live on PyPI under the
name `ramtable`.

Install from a local checkout:

```bash
python -m pip install .
```

Install in editable mode for development:

```bash
python -m pip install --editable .
```

## Quick start

```python
from ramtable import Table

people = Table(
    name="people",
    columns={
        "id": int,
        "name": str,
        "age": int,
        "email": str,
    },
)

# This table has no defaults, so every row needs all four columns.
people.rows.insert(
    {"id": 1, "name": "Ada", "age": 36, "email": "ada@example.com"}
)
people.rows.insert(
    {"id": 2, "name": "Linus", "age": 28, "email": "linus@example.com"}
)

print(people.rows.get_column("name"))
# ['Ada', 'Linus']

# Update every row matching the conditions; returns the number of rows changed.
updated = people.rows.update(
    where={"id": 1},
    values={"name": "Ada Lovelace"},
)
print(updated)
# 1

print(people.rows.get_one(0))
# {'id': 1, 'name': 'Ada Lovelace', 'age': 36, 'email': 'ada@example.com'}

# Conditions go beyond equality in filter(), update(), and delete().
older = people.rows.filter({"age": {">": 30}})
print([row["name"] for row in older])
# ['Ada Lovelace']
```

A `Table` exposes two views over the same storage:

- `table.rows`: the data. Insert, read, update, and remove rows.
- `table.columns`: the schema. Add, remove, and retype columns.

The [user guide](docs/guide.md) documents every operation.

## Features

- **Explicit schema:** declare column names and types when the table is
  created.
- **Runtime validation:** every row must contain every schema column without
  an insert default, and each value must match its declared type.
- **Row operations:** insert, retrieve, update, filter, and delete rows.
- **Insert defaults:** declare optional column defaults at table creation so
  inserted rows can omit those columns.
- **Flexible conditions:** one condition format powers `filter`, `update`,
  and `delete`, with comparison, membership, and string operators.
- **Schema evolution:** add, remove, or retype columns while accounting for
  existing rows.
- **Validate-then-write:** RAMTable checks update requests in full before
  any row changes.
- **Zero dependencies:** install the package and start.

## Supported types

Besides plain classes, RAMTable understands `Any`, `None`, unions
(`str | None`), `Annotated`, `Literal`, `type[T]`, and parameterized lists,
sets, frozensets, sequences, mappings, dictionaries, and tuples. Nested
arguments are checked recursively:

| Annotation | Example | Rule |
|---|---|---|
| Classes | `int`, `str`, `bytes` | `isinstance` |
| Unions | `str \| None` | any alternative may match |
| `Literal` | `Literal["pending", "done"]` | value and exact type |
| Sequence types | `list[str]`, `set[int]`, `Sequence[float]` | container class, then every item |
| Mapping types | `dict[str, int]`, `Mapping[str, list[int]]` | container class, then every key and value |
| Tuples | `tuple[int, str]`, `tuple[int, ...]` | fixed positions or one repeated type |
| `Annotated` | `Annotated[int, "id"]` | base type only; metadata is ignored |
| Class objects | `type[int]` | subclasses of `T` |
| `Any` / `None` | n/a | any value / only `None` |

```python
from typing import Literal
from ramtable import Table

events = Table(
    "events",
    {
        "name": str,
        "status": Literal["pending", "complete"],
        "tags": list[str],
    },
)
```

Simple classes follow `isinstance` semantics, so a `bool` value also matches
`int`. `Literal` is stricter: it compares both value and exact type. See
[types and validation](docs/types-and-validation.md) for the complete rules
and known limitations.

## Copies and lifecycle

RAMTable stores rows as dictionaries. `insert()` keeps a shallow copy of the
dictionary you pass, and reading a row returns a new dictionary with the same
values. Mutable cell values stay shared between your code and the table.

Insert defaults work differently: RAMTable deep-copies them at creation,
when a row omits the column, and when `columns.get_default()` returns them.

`table.clear()` removes every row and keeps the schema and insert defaults.
RAMTable never writes to disk, so records disappear when the process ends.

## Documentation

| Document | Contents |
|---|---|
| [User guide](docs/guide.md) | Tables, rows, filtering, schema changes, errors, and limits. |
| [API reference](docs/api.md) | Every class and method, with arguments, returns, and exceptions. |
| [Types and validation](docs/types-and-validation.md) | Supported annotations and runtime checking rules. |
| [Development and releases](docs/development.md) | Project layout, checks, and the release process. |
| [CHANGELOG](CHANGELOG.md) | Release history. |
| [LICENSE](LICENSE) | MIT license terms. |

## Project status

RAMTable lives on [PyPI](https://pypi.org/project/ramtable/) and
[TestPyPI](https://test.pypi.org/project/ramtable/) as `ramtable`. Use PyPI
for stable releases and TestPyPI to try release candidates and other
pre-releases. The PyPI badge above shows the latest published version; the
[CHANGELOG](CHANGELOG.md) records the full release history.

## License

RAMTable uses the MIT License. See [LICENSE](LICENSE) for the terms.
