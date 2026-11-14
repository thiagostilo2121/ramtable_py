# RAMTable

RAMTable stores typed rows in memory. You declare a schema, and the table
validates every value you insert or update. It has no runtime dependencies.

## Quick start

Install RAMTable with `python -m pip install ramtable`, then create a table,
insert rows, update one, and filter the rest:

```python exec="on" source="above" result="text"
--8<-- "examples/quick_start.py"
```

The documentation build executes this example, so the output above matches the
code in the repository.

[Start with the user guide](guide/index.md) or read the
[API reference](reference/index.md).
