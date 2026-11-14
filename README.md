# RAMTable

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
[![PyPI](https://img.shields.io/pypi/v/ramtable)](https://pypi.org/project/ramtable/)
[![TestPyPI](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Ftest.pypi.org%2Fpypi%2Framtable%2Fjson&label=TestPyPI&query=%24.info.version&color=blue)](https://test.pypi.org/project/ramtable/)

RAMTable stores typed tables in memory for data that lives as long as the
program. You declare a schema, and the table validates every row.

The library has no runtime dependencies. Data stays in memory and disappears
when the process ends. RAMTable executes no SQL and writes nothing to disk.

## Installation

Use Python 3.11 or later. Install the latest stable release from PyPI:

```bash
python -m pip install ramtable
```

Pre-releases live on TestPyPI. The documentation covers that index, local
checkouts, and editable installs.

## Example

```python
from ramtable import Table

people = Table(
    name="people",
    columns={"id": int, "name": str, "age": int},
)

people.rows.insert({"id": 1, "name": "Ada", "age": 36})
people.rows.insert({"id": 2, "name": "Linus", "age": 28})

print(people.rows.get_column("name"))
# ['Ada', 'Linus']

older = people.rows.filter({"age": {">": 30}})
print([row["name"] for row in older])
# ['Ada']
```

## Documentation

Full documentation, including the user guide, API reference, and release
notes: <https://thiagostilo2121.github.io/ramtable_py/>

RAMTable uses the MIT License. See [LICENSE](LICENSE) for the terms.
