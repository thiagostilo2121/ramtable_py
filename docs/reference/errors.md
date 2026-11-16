# Errors

RAMTable raises standard Python exceptions with descriptive messages. Each
method's `Raises` section in the [API reference](index.md) documents its
exact conditions. This page groups every exception by cause.

## Exception taxonomy

| Exception | Cause | Methods |
|---|---|---|
| `ValueError` | Invalid table name. | `Table()` |
| `ValueError` | Invalid schema. | `Table()`, `Columns()` |
| `ValueError` | Invalid column name. | `Table()`, `Columns()` |
| `ValueError` | Invalid column name. | `Columns.add()` |
| `ValueError` | Unknown default column. | `Table()`, `Columns()` |
| `ValueError` | Column already exists. | `Columns.add()` |
| `ValueError` | Missing fill value. | `Columns.add()` |
| `ValueError` | Column does not exist. | `Columns.get()`, `Columns.remove()` |
| `ValueError` | Column does not exist. | `Columns.update()` |
| `ValueError` | Column does not exist. | `Columns.set_default()` |
| `ValueError` | Column does not exist. | `Columns.get_default()` |
| `ValueError` | Column does not exist. | `Columns.remove_default()` |
| `ValueError` | Column does not exist. | `Rows.get_column()` |
| `ValueError` | Column does not exist. | `Rows.get_columns()` |
| `ValueError` | Column does not exist. | `Rows.filter()`, `Rows.delete()` |
| `ValueError` | Column does not exist. | `Rows.update()` |
| `ValueError` | Cannot remove last column. | `Columns.remove()` |
| `ValueError` | No insert default. | `Columns.get_default()` |
| `ValueError` | No insert default. | `Columns.remove_default()` |
| `ValueError` | Wrong row columns. | `Rows.insert()`, `Rows.remove()` |
| `ValueError` | Row not found. | `Rows.remove()` |
| `ValueError` | Invalid conditions. | `Rows.filter()`, `Rows.delete()` |
| `ValueError` | Invalid conditions. | `Rows.update()` |
| `ValueError` | Invalid update values. | `Rows.update()` |
| `TypeError` | Unsupported annotation. | `Table()`, `Columns()` |
| `TypeError` | Unsupported annotation. | `Columns.add()` |
| `TypeError` | Unsupported annotation. | `Columns.update()` |
| `TypeError` | Existing value does not match. | `Columns.update()` |
| `TypeError` | Default does not match. | `Columns.update()` |
| `TypeError` | Defaults not a dictionary. | `Table()`, `Columns()` |
| `TypeError` | Row not a dictionary. | `Rows.insert()`, `Rows.remove()` |
| `TypeError` | Value does not match type. | `Rows.insert()`, `Rows.remove()` |
| `TypeError` | Assigned value does not match type. | `Rows.update()` |
| `TypeError` | Invalid default. | `Table()`, `Columns()` |
| `TypeError` | Invalid fill value or default. | `Columns.add()` |
| `TypeError` | Invalid default. | `Columns.set_default()` |
| `TypeError` | Cannot deep-copy value or default. | `Table()`, `Columns()` |
| `TypeError` | Cannot deep-copy value or default. | `Columns.add()` |
| `TypeError` | Cannot deep-copy value or default. | `Columns.set_default()` |
| `TypeError` | Cannot deep-copy value or default. | `Columns.get_default()` |
| `TypeError` | Cannot deep-copy value or default. | `Columns.get_defaults()` |
| `TypeError` | Invalid row index. | `Rows.get()`, `Rows.get_one()` |
| `TypeError` | Incompatible operand. | `Rows.filter()`, `Rows.delete()` |
| `TypeError` | Incompatible operand. | `Rows.update()` |
| `IndexError` | Out-of-range row index. | `Rows.get()`, `Rows.get_one()` |
