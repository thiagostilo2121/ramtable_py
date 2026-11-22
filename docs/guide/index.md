# User guide

RAMTable holds temporary data in typed tables. This guide covers creating
tables, inserting and reading rows, filtering, changing the schema, and the
copy rules that apply to cell values.

Each page stands on its own with runnable examples. For exact signatures and
exceptions, see the [API reference](../reference/index.md).

## Contents

- [Create a table](create-table.md): schema, supported types, and insert
  defaults.
- [Insert and read rows](rows.md): `insert`, `insert_many`, retrieval, and
  the copy rules for cell values.
- [Filter rows](filtering.md): the condition format shared by `filter`,
  `update`, and `delete`.
- [Update and delete rows](updating-deleting.md): `update`, `remove`,
  `delete`, `pop`, and `clear`.
- [Change the schema](schema.md): add, remove, and retype columns, and
  inspect the current schema.

## Scope and limitations

RAMTable is a local in-memory container:

- it does not persist data between runs;
- it provides no SQL, indexes, or uniqueness constraints; filters cover
  common comparisons, membership, and string matching, but not joins or
  aggregation;
- it implements no transactions, no concurrent storage, and no
  synchronization across processes;
- it is not a replacement for a database when durability, complex queries,
  or coordination between multiple users are required.

Use it when the data lives as long as the program and the schema and row
operations give you enough structure.

## Errors

RAMTable raises standard Python exceptions with descriptive messages.
`ValueError` covers invalid names, arguments, row structure, unknown
columns, and unknown operators. `TypeError` covers unsupported annotations,
values that do not match their column type, copy failures, and invalid
indexes. `IndexError` covers row indexes outside the table.

The [errors reference](../reference/errors.md) lists every cause and the
methods that raise it.
