# Development and releases

This document summarizes the repository layout, the local workflow, and
how to prepare a release. It does not change or extend the RAMTable API.

## Contents

- [Project layout](#project-layout)
- [Set up a local environment](#set-up-a-local-environment)
- [Build distributions](#build-distributions)
- [Versioning](#versioning)
- [Preparing a release](#preparing-a-release)
- [Project status](#project-status)

## Project layout

```text
.
├── .github/
│   └── workflows/
│       ├── publish-test.yml
│       ├── publish.yml
│       └── tests.yml
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
│   ├── api.md
│   ├── development.md
│   ├── guide.md
│   └── types-and-validation.md
└── test_table.py
```

- `src/ramtable/`: installable package implementation.
- `test_table.py`: executable example of basic library usage.
- `docs/`: user guide, API reference, and behavior documentation.
- `pyproject.toml`: project metadata and build backend configuration.
- `.github/workflows/`: continuous integration and publication workflows.

## Set up a local environment

Python 3.11 or later is required. Install the project in editable mode:

```bash
python -m pip install --editable .
```

Run the example from the repository root:

```bash
python test_table.py
```

Expected output:

```text
['Alice', 'Bob']
['Alicia', 'Bob']
```

The repository currently contains an executable example rather than an
automated test suite. GitHub Actions runs byte-compilation and import checks
on every supported Python version, plus package validation for release pull
requests. When tests are added, document the official command here and run
them before releasing.

## Build distributions

The build backend declared in `pyproject.toml` is Hatchling. With `build`
installed, build a wheel and source distribution from the repository root:

```bash
python -m build
```

Artifacts are written to `dist/`. Verify that the wheel contains the
`ramtable` package and that its metadata reports the intended version.

## Versioning

The project follows PEP 440. Versions take one of three forms depending on
the branch:

| Branch | Version form | Example | Published to |
|---|---|---|---|
| `dev` | `X.Y.Z.devN` | `0.3.2.dev0` | nothing |
| `test_pypi` | `X.Y.ZrcN` or `X.Y.Z` | `0.3.1rc0`, `0.3.1` | TestPyPI |
| `main` | `X.Y.Z` | `0.3.1` | PyPI |

`MAJOR.MINOR.PATCH` follows semantic versioning:

- `PATCH` for compatible fixes;
- `MINOR` for compatible functionality;
- `MAJOR` for breaking API or behavior changes.

Development versions are never published. TestPyPI accepts release
candidates and stable versions, so the final stable release can be tested
there before it reaches PyPI. PyPI accepts stable versions only.

## Preparing a release

1. On `dev`, update `project.version` in `pyproject.toml` and add the
   corresponding section to `CHANGELOG.md`.
2. Check that the README and documentation describe current behavior.
3. Run the example and all available build/test checks.
4. Build and inspect the wheel and source distribution.
5. Open a pull request from `dev` to `test_pypi`. The pull request validates
   and builds the distributions without publishing. Merging it publishes the
   validated artifact to TestPyPI.
6. Test the release candidate. To publish the final stable version, set the
   stable `X.Y.Z` version on `dev`, open another pull request to
   `test_pypi`, and merge it so the stable artifact is also tested on
   TestPyPI.
7. Open a pull request from `test_pypi` to `main`. Merging it publishes the
   validated artifact to PyPI.

Publication uses PyPI Trusted Publishing with GitHub Actions OIDC. No API
tokens or repository secrets are required; the publisher and environment are
configured on PyPI and TestPyPI. See the workflow files in
`.github/workflows/` for the exact behavior.

## Project status

RAMTable is in early development. New capabilities should be documented in
the changelog and API reference when they become part of a release. Future
plans are not compatibility guarantees or delivery-date commitments.
