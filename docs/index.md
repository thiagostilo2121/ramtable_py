# RAMTable

RAMTable stores typed rows in memory. You declare a schema, and the table
validates every value you insert or update. It has no runtime dependencies.
Data lives as long as the process: RAMTable executes no SQL and writes
nothing to disk.

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

Typical uses include intermediate results of a multi-step process, temporary
records staged during a calculation or import, the working set of a
long-running task, and prototypes that want typed rows before a database
exists.

For simple collections, use a list or dictionary. If data must survive
restarts, be shared between processes, or be queried with SQL, use a
persistence layer. For analysis and vectorized operations, use a data-frame
library.

## Features

- **Explicit schema and validation:** every row must contain every column
  without an insert default, and each value must match its declared type.
- **Row operations:** insert, retrieve, update, filter, and delete. One
  condition format powers `update`, `filter`, and `delete`, with comparison,
  membership, and string operators.
- **Insert defaults and schema changes:** declare defaults for optional
  columns, and add, remove, or retype columns while accounting for existing
  rows.
- **Zero dependencies:** install the package and start.

## Installation

RAMTable requires Python 3.11 or later. Install the stable release:

```bash
python -m pip install ramtable
```

[Installation](guide/installation.md) covers pre-releases and local
checkouts.

## Quick start

Create a table, insert rows, update one, and filter the rest:

```python exec="on" source="above" result="text"
--8<-- "examples/quick_start.py"
```

The documentation build executes this example, so the output above matches the
code in the repository.

[Start with the user guide](guide/index.md) or read the
[API reference](reference/index.md).
