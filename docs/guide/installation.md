# Installation

RAMTable requires Python 3.11 or later. The package has no runtime
dependencies.

## Install from PyPI

Install the latest stable release:

```bash
python -m pip install ramtable
```

## Try a pre-release

TestPyPI hosts pre-releases. Stable releases live on PyPI under the name
`ramtable`; TestPyPI is a separate testing index.

```bash
python -m pip install --pre --index-url https://test.pypi.org/simple/ ramtable
```

## Install from a local checkout

From the repository root:

```bash
python -m pip install .
```

Install in editable mode while developing the package:

```bash
python -m pip install --editable .
```

The [development guide](../project/development.md) covers the `dev` extra,
the test suite, and the documentation build.

## Next steps

The [home page](../index.md) has a runnable example. The
[user guide](index.md) documents every table operation, and the
[API reference](../reference/index.md) covers signatures and exceptions.
