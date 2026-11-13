# Types and validation

RAMTable checks annotations when a schema changes and values when rows are
inserted or assigned. It never converts data; the checks run at runtime.

## Contents

- [Supported annotations](#supported-annotations)
- [Checking annotation support](#checking-annotation-support)
- [When RAMTable validates values](#when-ramtable-validates-values)
- [Validation failures](#validation-failures)

## Supported annotations

### Classes and general types

RAMTable accepts any Python class:

```python
int
str
bool
bytes
object
```

Simple class checks use `isinstance`, so subclass rules apply: `True`
matches `int` because `bool` subclasses `int`.

The following are also supported:

- `Any`: accepts any value.
- `None`: accepts only the `None` object.
- `type[T]`: accepts class objects that are subclasses of `T`.

For `type[T]`, `T` must be a class suitable for `isinstance`/`issubclass`.

### Unions

Use either `typing.Union` or Python's union syntax:

```python
str | None
int | float
```

A value must satisfy at least one alternative, and every alternative must be
a supported type.

### `Annotated`

`Annotated` validates its base type:

```python
from typing import Annotated

Annotated[int, "positive id"]
```

> [!NOTE]
> RAMTable ignores metadata: it runs no validators and enforces no
> constraints. `Annotated[int, ...]` validates like `int`.

### `Literal`

RAMTable supports non-empty `Literal` annotations:

```python
from typing import Literal

Literal["pending", "ready"]
Literal[1, 2, 3]
```

A value matches when it is equal to one of the options and has the exact
same type. For example, `True` does not match `Literal[1]`, even though
`True == 1`.

### Collections

RAMTable supports parameterized and unparameterized forms of:

| Annotation | Rule for parameterized forms |
|---|---|
| `list[T]` | The value must be a list, and every item must match `T`. |
| `set[T]`, `Set[T]` | The value must be a `set`, and every item must match `T`. |
| `frozenset[T]` | The value must be a `frozenset`, and every item must match `T`. |
| `Sequence[T]` | The value must satisfy `collections.abc.Sequence`, and every item must match `T`. |
| `AbstractSet[T]` | The value must satisfy `collections.abc.Set` (for example, a `set` or `frozenset`), and every item must match `T`. |
| `dict[K, V]` | The value must be a `dict`; keys and values are validated recursively. |
| `Mapping[K, V]` | The value must satisfy `collections.abc.Mapping`; keys and values are validated recursively. |

Unparameterized forms (such as `list` or `dict`) check the container class
without inspecting its elements. An empty container of the right class
satisfies a parameterized form; it has no elements to contradict the
annotation.

Parameterized sequences and sets accept one type argument. Mappings accept
two type arguments.

### Tuples

Tuples can be checked without parameters, with fixed positional types, or
with one repeated element type:

```python
tuple
tuple[int, str]
tuple[int, ...]
```

- `tuple[int, str]` requires length two and checks each position against
  its corresponding type.
- `tuple[int, ...]` permits any length and checks every item as `int`.
- `tuple` checks only that the value is a tuple.

## Checking annotation support

`TypeValidator.is_supported_type(annotation)` reports whether RAMTable
understands an annotation form. `Table` and `Columns` use this check when
creating or changing a schema. Declaring an unsupported form as a column
type raises `TypeError`.

The annotation form matters. A type existing in the `typing` module does not
mean RAMTable implements its semantics.

## When RAMTable validates values

- **`Rows.insert(row)`**: checks that the object is a dictionary, fills
  omitted columns that have an insert default, then checks that the
  resulting keys exactly match the schema and that each value matches its
  column's annotation. RAMTable validates insert defaults at creation.
- **`Rows.remove(row)`**: performs the same validation before looking for
  an equal row.
- **`Rows.update(where, values)`**: checks condition columns and operators,
  and validates assigned values. Python evaluates condition values directly;
  it does not check them against the declared types.
- **`Rows.filter(where)` and `Rows.delete(where)`**: check condition
  columns and operators. They do not check condition values against column
  types.
- **`Table(..., defaults)`**: validates each insert default against its
  column type at creation. It rejects defaults for unknown columns and
  raises `TypeError` for defaults it cannot deep-copy.
- **`Columns.add(name, type, fill_value)`**: validates `fill_value` when
  provided. A fill value is required when rows already exist.
- **`Columns.update(name, new_type)`**: checks that every existing value
  in the column and its insert default, if any, match the new type before
  changing the schema.

RAMTable never converts values. Inserting `"5"` into an `int` column raises
`TypeError`.

## Validation failures

- `TypeError`: unsupported annotation, non-dictionary row, incompatible
  cell value, incompatible update value, or non-integer row index.
- `ValueError`: missing or unknown row keys, non-existent column, empty
  filter or update arguments, unknown filter operator, or update arguments
  that do not satisfy the required structure.
- `IndexError`: row index out of range.

See the [API reference](api.md) for the exceptions each method can raise.
