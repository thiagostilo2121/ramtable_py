# Development and releases

This document summarizes the repository layout and how to prepare a release.
It does not change or extend the RAMTable API.

## Project layout

```text
.
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── src/
│   └── ramtable/
│       ├── __init__.py
│       ├── columns.py
│       ├── rows.py
│       ├── table.py
│       └── types.py
├── docs/
└── test_table.py
```

- `src/ramtable/`: installable package implementation.
- `test_table.py`: executable example of basic library usage.
- `docs/`: user guide, API reference, and behavior documentation.
- `pyproject.toml`: project metadata and build backend configuration.

## Set up a local environment

Python 3.10 or later is required. Install the project in editable mode:

```bash
python -m pip install --editable .
```

Run the example from the repository root:

```bash
python test_table.py
```

Expected output includes:

```text
['Alice', 'Bob']
['Alicia', 'Bob']
```

The repository currently contains an executable example rather than an
automated test suite. When tests are added, document the official command here
and run them before releasing.

## Build distributions

The build backend declared in `pyproject.toml` is Hatchling. With `build`
installed, build a wheel and source distribution from the repository root:

```bash
python -m build
```

Artifacts are written to `dist/`. Verify that the wheel contains the
`ramtable` package and that its metadata reports the intended version.

## Versioning

The project uses `MAJOR.MINOR.PATCH` versions:

- `PATCH` for compatible fixes;
- `MINOR` for compatible functionality;
- `MAJOR` for breaking API or behavior changes.

Before a release:

1. Update `project.version` in `pyproject.toml`.
2. Add a section for the version and its changes at the top of
   `CHANGELOG.md`.
3. Check that the README and documentation describe current behavior.
4. Run the example and all available build/test checks.
5. Build and inspect the wheel and source distribution.
6. Publish to TestPyPI first to validate the distribution; publish to official
   PyPI only when the release is approved.

Do not commit passwords, tokens, or credentials. Use the publishing service's
secrets and review the GitHub Actions workflow before enabling a release.

## Project status

RAMTable is in early development. New capabilities should be documented in
the changelog and API reference when they become part of a release. Future
plans are not compatibility guarantees or delivery-date commitments.
