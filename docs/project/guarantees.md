# 1.0 guarantees

The 1.0 release freezes the public contract described on this page. Later
`1.x` releases keep it. Apart from security fixes, changes that break it
wait for `2.0.0` and follow the [deprecation policy](deprecation.md).

## Public API

The public API covers:

- the names in `ramtable.__all__`: `Columns`, `Rows`, `Table`,
  `TypeValidator`, and `__version__`;
- the methods, attributes, and properties documented on those classes;
- the names in the `ramtable` package root and the documented import paths.

Private names, names that start with an underscore, and helpers listed under
[Internal helpers](../reference/index.md#internal-helpers) stay outside the
contract.

## What 1.0 freezes

### Signatures

Every documented public call keeps its parameter names, order, defaults,
keyword-only markers, and return type. A compatible addition, such as a new
method or a new optional parameter with a default, can arrive in a minor
release. Removing a parameter, renaming it, making it required, or changing
its type is a breaking change.

### Error taxonomy

Each documented failure keeps its exception class and the condition that
raises it. The [errors reference](../reference/errors.md) is the canonical
list. Message text can change when it improves clarity; the exception class
and the failing condition cannot.

Code that catches `TypeError`, `ValueError`, or `IndexError` from a documented
operation continues to work.

### Copy semantics

Row copies and container copies keep the documented behavior:

- `insert` and `insert_many` store shallow copies of each row dictionary.
  Reads and `pop` return shallow copies. Mutable values inside the dictionary
  keep their identity.
- `Columns.add(fill_value=...)` deep-copies the fill value for each existing
  row.
- Insert defaults are deep-copied when set, once per row that omits the
  column, and when `get_default` or `get_defaults` returns them.
- Returned lists and dictionaries from `get_columns` and `get_column` are new
  containers whose items keep their identity.

A caller can rely on mutating a returned row dictionary without changing the
stored row, and on changing a shared nested object to affect every row that
holds it.

### TypeValidator

`TypeValidator.is_supported_type` and `TypeValidator.matches_type` keep their
behavior for every form listed in
[Supported annotations](../reference/types-and-validation.md#supported-annotations).
That includes `Any`, `None`, plain classes, unions, `Annotated`, `Literal`,
parameterized and bare collections, fixed and variadic tuples, and `type[T]`.

New releases can accept more annotation forms. They do not change the result
for a form that `is_supported_type` already reports as supported. Unsupported
forms stay outside the contract.

### Version format and channels

Versions follow `MAJOR.MINOR.PATCH` as described on the
[releases page](releases.md). Development builds use `X.Y.ZdevN` and are not
published. Release candidates use `X.Y.ZrcN` and go to TestPyPI. Stable
releases use `X.Y.Z` and go to PyPI.

The project publishes through the existing branches:

```text
dev → test_pypi → main
```

The installed distribution reports its version through
`ramtable.__version__`.

## What 1.0 does not freeze

These details can change in any release:

- error message wording;
- internal helpers, private attributes, and module-level constants that do
  not start with a public name;
- performance and memory use;
- the order of items in `__all__`;
- object representations and generated documentation layout;
- behavior for input the documentation does not support;
- the exact output of `scripts/` tools and the documentation build.

## Adding to the contract

A new public symbol starts its own contract at the release where it first
appears. Existing symbols keep theirs. Removing either follows the
[deprecation policy](deprecation.md).
