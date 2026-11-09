# RAMTable

RAMTable provides typed in-memory tables for data that only needs to live
while a program is running. It gives records an explicit schema and common
operations without requiring you to manage lists and dictionaries by hand or
set up a persistent SQL database.

RAMTable is a lightweight Python library with no runtime dependencies. Data is
kept in memory and is lost when the process ends. RAMTable is not a database,
does not execute SQL, and does not write data to disk.

## Why RAMTable?

RAMTable is useful when temporary data needs more structure than a plain list
or dictionary, for example:

- intermediate results during a process;
- temporary records during a calculation or import;
- data used by a running task;
- prototypes that need typed rows and columns without a persistent database.

For simple collections, a list or dictionary may still be the better choice.
If data must survive process restarts, be shared between processes, queried
with SQL, or managed with database guarantees, use an appropriate persistence
solution instead.

## Project status

The current project version is **0.2.0**. RAMTable is available on
[TestPyPI](https://test.pypi.org/project/ramtable/) for testing and has not yet
been released on the official PyPI index. TestPyPI is a test environment and
should not be confused with PyPI.

RAMTable is at an early stage and will continue to evolve. See the
[CHANGELOG](CHANGELOG.md) for release history and updates.

## Requirements

- Python 3.10 or later.

## Installation

Install the version available from TestPyPI:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ ramtable
```

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

# Every row must contain exactly the columns defined above.
people.rows.insert(
    {"id": 1, "name": "Ada", "age": 36, "email": "ada@example.com"}
)
people.rows.insert(
    {"id": 2, "name": "Linus", "age": 28, "email": "linus@example.com"}
)

print(people.rows.get_column("name"))
# ['Ada', 'Linus']

# Update every row matching the conditions.
updated_count = people.rows.update(
    where={"id": 1},
    values={"name": "Ada Lovelace"},
)
print(updated_count)
# 1

print(people.rows.get_one(0))
# {'id': 1, 'name': 'Ada Lovelace', 'age': 36, 'email': 'ada@example.com'}
```

`Table` shares its storage between `table.columns` and `table.rows`. Insert,
query, and update records through `rows`; modify the schema through `columns`.
See the [user guide](docs/guide.md) for a step-by-step explanation.

## Main features

- **Explicit schema:** define column names and types when creating a table.
- **Runtime validation:** rows must contain exactly the schema's columns and
  their values must match the declared types.
- **Record operations:** insert, retrieve, update, and remove rows.
- **Schema operations:** add and remove columns or change their declared type,
  while accounting for existing records.
- **No implicit persistence:** no server, SQL setup, or runtime dependencies
  are required.

## Supported types

RAMTable supports Python classes and common annotations, including `Any`,
`None`, `Annotated`, unions (`str | None`), `Literal`, parameterized lists,
sets, dictionaries, sequences, mappings, and tuples. `type[T]` annotations are
also supported. Parameterized containers are checked recursively.

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

Simple class checks use `isinstance`; following Python semantics, a `bool`
value also matches `int`. `Literal` is stricter and checks both value and
exact type. See [types and validation](docs/types-and-validation.md) for
details and limitations.

## Copies and lifecycle

Rows are stored as dictionaries. Inserting a row makes a shallow copy of the
dictionary. Row retrieval also returns new dictionaries, but does not copy
their values. Mutable objects used as cell values may therefore remain shared
with the code that supplied or retrieved them.

`table.clear()` removes all records and preserves the schema. No operation
writes data to disk; records disappear when the process ends.

## Documentation

- [User guide](docs/guide.md): lifecycle, CRUD examples, schema, queries,
  errors, and library limitations.
- [Complete API reference](docs/api.md): classes, methods, arguments, return
  values, and exceptions.
- [Types and validation](docs/types-and-validation.md): supported annotations
  and runtime checking rules.
- [Development and releases](docs/development.md): project layout, checks, and
  preparing a release.
- [CHANGELOG](CHANGELOG.md): changes by version.
- [License](LICENSE): MIT.

## License

RAMTable is distributed under the MIT License. See [LICENSE](LICENSE) for
the terms.
