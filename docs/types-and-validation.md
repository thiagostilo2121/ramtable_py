# Types and validation

RAMTable validates annotations when a schema is created or changed, and
values when rows are inserted or assigned. Validation never converts data
and is not a replacement for a static type checker.

## Contents

- [Supported annotations](#supported-annotations)
- [Checking annotation support](#checking-annotation-support)
- [When values are validated](#when-values-are-validated)
- [Validation failures](#validation-failures)

## Supported annotations

### Classes and general types

Any Python class is accepted:

```python
int
str
bool
bytes
object
```

Simple class checks use `isinstance`. Consequently, normal subclass
relationships apply: `True` matches `int` because `bool` is a subclass of
`int`.

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

A value matches if it satisfies at least one alternative. Every
alternative in a union must be a supported type.

### `Annotated`

`Annotated` validates its base type:

```python
from typing import Annotated

Annotated[int, "positive id"]
```

> [!NOTE]
> Metadata is not interpreted: validators are not run, and constraints
> described by metadata are not enforced. For value validation,
> `Annotated[int, ...]` behaves exactly like `int`.

### `Literal`

Non-empty `Literal` annotations are supported:

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
without inspecting its elements. Empty containers satisfy parameterized
forms whenever the container class is correct, because there are no
elements that could contradict the annotation.

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

The annotation form matters: the fact that a type object exists in the
`typing` module does not mean RAMTable implements its semantics.

## When values are validated

- **`Rows.insert(row)`**: checks that the object is a dictionary, that its
  keys exactly match the schema, and that each value matches its column's
  annotation.
- **`Rows.remove(row)`**: performs the same validation before looking for
  an equal row.
- **`Rows.update(where, values)`**: checks condition columns and operators,
  and validates assigned values. Condition values are not checked against
  their declared types; they are evaluated directly by Python.
- **`Rows.filter(where)` and `Rows.delete(where)`**: check condition
  columns and operators. They do not validate condition values against
  column types.
- **`Columns.add(name, type, default)`**: validates `default` when
  provided. A default is required when rows already exist.
- **`Columns.update(name, new_type)`**: checks that every existing value
  in the column matches the new type before changing the schema.

Values are never converted automatically. If a column is declared as
`int`, inserting the string `"5"` fails; RAMTable does not convert it to
`5`.

## Validation failures

- `TypeError`: unsupported annotation, non-dictionary row, incompatible
  cell value, incompatible update value, or non-integer row index.
- `ValueError`: missing or unknown row keys, non-existent column, empty
  filter or update arguments, unknown filter operator, or update arguments
  that do not satisfy the required structure.
- `IndexError`: row index out of range.

See the [API reference](api.md) for the exceptions each method can raise.
