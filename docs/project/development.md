# Development and releases

Repository layout, local workflow, and release steps. Nothing here changes
the RAMTable API.

## Contents

- [Project layout](#project-layout)
- [Set up a local environment](#set-up-a-local-environment)
- [Build the documentation](#build-the-documentation)
- [Documentation deployment](#documentation-deployment)
- [Build distributions](#build-distributions)
- [Versioning](#versioning)
- [Preparing a release](#preparing-a-release)
- [Project status](#project-status)

## Project layout

```text
.
├── .github/
│   └── workflows/
│       ├── docs-notify.yml
│       ├── docs.yml
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
│   │   ├── index.md
│   │   └── installation.md
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
│   │   ├── license.md
│   │   └── releases.md
│   ├── stylesheets/
│   │   └── extra.css
│   ├── index.md
│   └── requirements.txt
├── scripts/
│   ├── check_built_site.py
│   └── generate_release_metadata.py
├── examples/
│   └── quick_start.py
├── tests/
│   ├── conftest.py
│   └── test_*.py
└── my_test.py            # local example, ignored by Git
```

- `src/ramtable/`: installable package implementation.
- `tests/`: pytest suite covering the public API and its behavior.
- `my_test.py`: optional local example of basic library usage; it is not
  tracked by Git.
- `docs/`: landing page, installation steps, user guide, API reference,
  validation rules, and project pages.
- `docs/reference/api/`: class pages generated from the package docstrings.
- `docs/project/`: development guide, release policy, changelog,
  contribution guide, and license. The changelog, contribution, and license
  pages include the matching files from the repository root.
- `zensical.toml`: site configuration for Zensical.
- `scripts/check_built_site.py`: verifies links and anchors in the built site.
- `scripts/generate_release_metadata.py`: reads the declared versions from
  Git, queries PyPI and TestPyPI, and writes the generated files for the
  releases page. The outputs are ignored by Git and recreated on every build.
- `examples/quick_start.py`: the quick start shown on the site home page. The
  documentation build executes it, and continuous integration runs it against
  the built wheel.
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

The documentation uses Zensical, mkdocstrings, and markdown-exec. The
executable examples import RAMTable, so install the package in the same
environment. Install the pinned documentation dependencies and the package in
a separate virtual environment:

```bash
python -m venv .venv-docs
source .venv-docs/bin/activate
python -m pip install -r docs/requirements.txt
python -m pip install --editable .
```

From the repository root, generate the release metadata and build the site
in strict mode:

```bash
python scripts/generate_release_metadata.py
zensical build --strict --clean
```

The generator reads `pyproject.toml` from `origin/main`, `origin/dev`, and
`origin/test_pypi`. A missing branch or an unreachable index leaves that
entry marked unavailable; the build still succeeds. Fetch all branches
before a local build if you want the current versions on every row.

The build writes to `site/`. Verify links, anchors, and assets:

```bash
python scripts/check_built_site.py
```

Strict mode reports Markdown problems, but it does not inspect links that
arrive through snippets. The checker reads the generated HTML and covers
those links.

GitHub Actions runs the test suite, byte-compilation, and import checks on
every supported Python version. It also builds the wheel, installs it into a
clean virtual environment, and runs `examples/quick_start.py`. Release pull
requests get package validation too. The docs workflow validates pull
requests to `main` and deploys from `main`; a notifier rebuilds the site when
`dev` or `test_pypi` changes `pyproject.toml`. Run the tests before
releasing.

## Documentation deployment

GitHub Pages serves the site from the `docs.yml` workflow. Set the Pages
source to GitHub Actions in the repository settings. The workflow deploys
only from `main`, and pull requests to `main` build without deploying.

The daily schedule refreshes release metadata. `docs-notify.yml` dispatches
a build from `main` when `dev` or `test_pypi` changes `pyproject.toml`. It
does not check out or run code from those branches. The first deploy needs
`zensical.toml` and `docs/` on `main`, so promote the documentation before
you change the Pages source. Require the Docs check in the `main` branch
protection rules so a broken build cannot merge.

## Build distributions

The build backend declared in `pyproject.toml` is Hatchling. With `build`
installed, build a wheel and source distribution from the repository root:

```bash
python -m build
```

The build writes artifacts to `dist/`. Check that the wheel contains the
`ramtable` package and that its metadata reports the intended version.

## Versioning

`pyproject.toml` `project.version` is the only source of truth. The
[releases page](releases.md) documents the version forms, publication
targets, and current branch versions.

The installed package exposes the version as `ramtable.__version__` through
its distribution metadata. The README uses a dynamic PyPI badge.
`CHANGELOG.md` records releases and is the only other file with version
numbers.

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
