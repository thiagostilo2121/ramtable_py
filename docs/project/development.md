# Development and releases

Repository layout, local workflow, and release steps. Nothing here changes
the RAMTable API.

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
├── AGENTS.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
├── README.md
├── zensical.toml
├── src/
│   └── ramtable/
│       ├── __init__.py
│       ├── columns.py
│       ├── rows.py
│       ├── table.py
│       └── types.py
├── docs/
│   ├── guide/
│   │   └── index.md
│   ├── reference/
│   │   ├── api/
│   │   │   ├── columns.md
│   │   │   ├── rows.md
│   │   │   ├── table.md
│   │   │   └── types.md
│   │   ├── index.md
│   │   └── types-and-validation.md
│   ├── project/
│   │   ├── changelog.md
│   │   ├── contributing.md
│   │   ├── development.md
│   │   └── license.md
│   ├── stylesheets/
│   │   └── extra.css
│   ├── index.md
│   └── requirements.txt
├── scripts/
│   └── check_built_site.py
├── tests/
│   ├── conftest.py
│   └── test_*.py
└── my_test.py            # local example, ignored by Git
```

- `src/ramtable/`: installable package implementation.
- `tests/`: pytest suite covering the public API and its behavior.
- `my_test.py`: optional local example of basic library usage; it is not
  tracked by Git.
- `docs/`: user guide, API reference, validation rules, and project pages.
- `docs/reference/api/`: class pages generated from the package docstrings.
- `docs/project/`: changelog, contribution guide, release process, and
  license. The changelog, contribution, and license pages include the
  matching files from the repository root.
- `zensical.toml`: site configuration for Zensical.
- `scripts/check_built_site.py`: verifies links and anchors in the built site.
- `CONTRIBUTING.md`: contribution guidelines.
- `LICENSE`: MIT license text.
- `AGENTS.md`: guidance for contributors using AI coding tools. It does not
  replace `CONTRIBUTING.md`.
- `pyproject.toml`: project metadata, development dependencies, and tool
  configuration.
- `.github/workflows/`: continuous integration and publication workflows.

## Set up a local environment

Use Python 3.11 or later. Install the project in editable mode with the
development dependencies:

```bash
python -m pip install --editable ".[dev]"
```

Run the test suite from the repository root:

```bash
python -m pytest
```

To include coverage information:

```bash
python -m pytest --cov=ramtable --cov-report=term-missing
```

Run the example from the repository root:

```bash
python my_test.py
```

The script prints the result of each operation.

## Build the documentation

The documentation uses Zensical and mkdocstrings. Install the pinned
documentation dependencies in a separate virtual environment:

```bash
python -m venv .venv-docs
source .venv-docs/bin/activate
python -m pip install -r docs/requirements.txt
```

From the repository root, build the site in strict mode and remove previous
output:

```bash
zensical build --strict --clean
```

The build writes to `site/`. Verify links, anchors, and assets:

```bash
python scripts/check_built_site.py
```

Strict mode reports Markdown problems, but it does not inspect links that
arrive through snippets. The checker reads the generated HTML and covers
those links.

GitHub Actions runs the test suite, byte-compilation, and import checks on
every supported Python version. Release pull requests also get package
validation. Run the tests before releasing.

## Build distributions

The build backend declared in `pyproject.toml` is Hatchling. With `build`
installed, build a wheel and source distribution from the repository root:

```bash
python -m build
```

The build writes artifacts to `dist/`. Check that the wheel contains the
`ramtable` package and that its metadata reports the intended version.

## Versioning

The project follows PEP 440. Versions take one of three forms depending on
the branch:

| Branch | Version form | Example | Published to |
|---|---|---|---|
| `dev` | `X.Y.ZdevN` | `0.4.0dev0` | nothing |
| `test_pypi` | `X.Y.ZrcN` or `X.Y.Z` | `0.4.0rc0`, `0.4.0` | TestPyPI |
| `main` | `X.Y.Z` | `0.4.0` | PyPI |

`MAJOR.MINOR.PATCH` follows semantic versioning:

- `PATCH` for compatible fixes;
- `MINOR` for compatible functionality;
- `MAJOR` for breaking API or behavior changes.

`pyproject.toml` holds the current version. The build backend and the GitHub
Actions workflows read it, and the installed package exposes it as
`ramtable.__version__` through its distribution metadata. The README uses a
dynamic PyPI badge. `CHANGELOG.md` is the only other file with version
numbers because it records releases.

Development versions are never published. TestPyPI accepts release
candidates and stable versions, so you can test the final stable release
there before it reaches PyPI. PyPI accepts stable versions only.

## Preparing a release

1. On `dev`, update `project.version` in `pyproject.toml`. This is the only
   place where the current version is defined. Add the corresponding
   section to `CHANGELOG.md`.
2. Check that the README and documentation describe current behavior. The
   README must not contain a hardcoded version.
3. Run the example, the test suite, and the build checks.
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

Publication uses PyPI Trusted Publishing with GitHub Actions OIDC. It needs
no API tokens or repository secrets; you configure the publisher and
environment on PyPI and TestPyPI. See the workflow files in
`.github/workflows/` for the exact behavior.

## Project status

RAMTable is in early development. Document new capabilities in the changelog
and API reference when they ship. Future plans are not compatibility
guarantees.
