# Deprecation policy

RAMTable keeps public symbols working after it stops recommending them. This
page defines how a deprecation starts, how long it lasts, and what the notice
says.

## Minimum permanence

A deprecated public symbol stays available for at least one complete minor
release after the release that announces the deprecation. A symbol announced
as deprecated in `1.2.0` keeps working through `1.3.x` and can be removed in
`2.0.0`.

Outside a security fix, removal happens only in a major release. A minor or
patch release never removes a deprecated public symbol. That release names
the affected symbol, the risk, and the replacement.

## Procedure

1. Add the replacement and document it in the user guide and API reference.
2. Mark the old symbol in its docstring with a `Deprecated:` note. Name the
   version that introduced the deprecation and the replacement.
3. Emit a `DeprecationWarning` from the code path that uses the old symbol.
4. Add a `Deprecated` entry to `CHANGELOG.md`. Name the symbol, the
   replacement, and the first version that can remove it.
5. Keep tests for the deprecated behavior until the symbol is removed.

Removal follows the same sequence in reverse: delete the code, the tests, and
the documentation, then record the removal under `Removed` in the changelog.

## Warning format

Deprecation warnings use this message shape:

```text
RAMTable: <symbol> is deprecated since <version> and will be removed in <version>; use <replacement> instead.
```

For example:

```python
import warnings

warnings.warn(
    "RAMTable: Rows.fetch_all() is deprecated since 1.2.0 and will be "
    "removed in 2.0.0; use Rows.get() instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

The message starts with `RAMTable:`, names the symbol exactly as the public
API does, gives both versions in PEP 440 form, and names one replacement.
Raise the warning with `stacklevel=2` or higher so it points at the caller.

## What is not a deprecation

These changes do not need a deprecation period:

- fixing a bug that made a documented operation behave incorrectly;
- changing an error message without changing the exception class;
- changing internal helpers or private attributes;
- rejecting input that the documentation never supported.

Changes to documented behavior follow the same rule as removals. The project
fixes the behavior in a major release and documents why, or it treats the
change as a bug fix.

## Current deprecations

The 1.0 release removes nothing and deprecates nothing.
