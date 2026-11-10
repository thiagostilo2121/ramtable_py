# RAMTable

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
[![PyPI](https://img.shields.io/pypi/v/ramtable)](https://pypi.org/project/ramtable/)
[![TestPyPI](https://img.shields.io/badge/TestPyPI-ramtable-orange)](https://test.pypi.org/project/ramtable/)

RAMTable provides typed in-memory tables for data that only needs to live
while a program is running. It gives records an explicit schema and common
operations, without requiring you to manage lists and dictionaries by hand
or set up a persistent SQL database.

RAMTable is a lightweight Python library with no runtime dependencies. Data
is kept in memory and is lost when the process ends. RAMTable is not a
database: it does not execute SQL and does not write data to disk.

## Where it fits

Reach for RAMTable when a plain `list` or `dict` does not provide enough
structure, but a persistent database is too much:

| | Plain `list` / `dict` | RAMTable | SQL database |
|---|:---:|:---:|:---:|
| Schema with declared types | — | ✓ | ✓ |
| Rows validated on write | — | ✓ | ✓ |
| Schema changes with data present | manual | ✓ | ✓ |
| Query language, indexes, constraints | — | — | ✓ |
| Survives process exit | — | — | ✓ |
| Setup | none | none | server or files |

Typical scenarios:

- intermediate results of a multi-step process;
- temporary records staged during a calculation or import;
- the working set of a long-running task;
- prototypes that want typed rows before a real database exists.

For simple collections, a list or dictionary is still the right answer. If
data must survive restarts, be shared between processes, or be queried with
SQL, use an appropriate persistence solution instead. For analysis and
vectorized operations, use a data-frame library: RAMTable targets structured
temporary storage, not analytics.

## Installation

RAMTable requires Python 3.11 or later.

Install the latest stable release from PyPI:

```bash
python -m pip install ramtable
```

Pre-releases are published to TestPyPI. To try one:

```bash
python -m pip install --pre --index-url https://test.pypi.org/simple/ ramtable
```

TestPyPI is a separate testing index, not the official package index. Stable
releases are published to PyPI under the name `ramtable`.

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

# Every row must contain exactly the columns declared above.
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

The [user guide](docs/guide.md) walks through every operation step by step.

## Features

- **Explicit schema:** declare column names and types when the table is
  created.
- **Runtime validation:** every row must contain exactly the schema's
  columns, and each value must match its declared type.
- **Row operations:** insert, retrieve, update, filter, and delete rows.
- **Flexible conditions:** one condition format powers `filter`, `update`,
  and `delete`, with comparison, membership, and string operators.
- **Schema evolution:** add, remove, or retype columns while accounting for
  existing rows.
- **Validate-then-write:** update requests are checked in full before any
  row is modified, so a rejected request never leaves a partial change.
- **Zero dependencies:** no server, no SQL setup, nothing beyond the package
  itself.

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
| `Any` / `None` | — | any value / only `None` |

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

Rows are stored as dictionaries. Inserting a row stores a shallow copy of
the dictionary; retrieving a row returns a new dictionary containing the same
values. Mutable objects used as cell values may therefore remain shared
with the code that supplied or retrieved them.

`table.clear()` removes all rows and preserves the schema. No operation
writes to disk: records disappear when the process ends.

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

RAMTable is published as `ramtable` on
[PyPI](https://pypi.org/project/ramtable/) and
[TestPyPI](https://test.pypi.org/project/ramtable/). Use PyPI for stable
releases and TestPyPI to try release candidates and other pre-releases. The
PyPI badge above shows the latest published version; the
[CHANGELOG](CHANGELOG.md) records the full release history.

The project is at an early stage and will continue to evolve. See the
[CHANGELOG](CHANGELOG.md) for release history.

## License

RAMTable is distributed under the MIT License. See [LICENSE](LICENSE) for
the terms.
