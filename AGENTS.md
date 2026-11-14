# AGENTS.md

RAMTable is a zero-dependency Python 3.11+ in-memory typed table library.
Package code is in `src/ramtable/`, tests in `tests/`.

## Setup and checks

- Install: `python -m pip install --editable ".[dev]"` (the `dev` extra adds
  only `pytest` and `pytest-cov`).
- Run everything: `python -m pytest` (`testpaths` is already `tests`).
- One test: `python -m pytest tests/test_rows.py::test_name`.
- Full CI equivalent: `python -m compileall -q src/ramtable`,
  `python -c "from ramtable import Columns, Rows, Table"`, then
  `python -m pytest -ra --cov=ramtable --cov-report=term-missing`.
- CI covers Python 3.11–3.15; a local venv may only have 3.14. Do not use
  syntax or APIs newer than 3.11.
- No linter, formatter, or type checker is configured. Do not add one to
  `pyproject.toml` unless asked. Match the existing style: 4 spaces, lines
  near 79 columns, type hints, and docstrings with `Args`/`Returns`/`Raises`.
- Docs dependencies are pinned in `docs/requirements.txt`, not in a
  `pyproject.toml` extra. Install them, then build:
  `python -m pip install -r docs/requirements.txt`,
  `python scripts/generate_release_metadata.py`,
  `zensical build --strict --clean`, `python scripts/check_built_site.py`.
  Use a virtual environment with RAMTable installed editable; the
  mkdocstrings pages import the package.

## Architecture

- `Table` creates one `storage` list and passes it to both `Columns` and
  `Rows`. Schema changes and row operations act on that same list.
- Keep validate-then-write semantics: `Columns.add/remove/update` and
  `Rows.update` must fully validate before mutating any row.
- `Rows._filter` is the single condition engine behind `filter`, `update`,
  and `delete`; operators live in the `_FILTER_OPERATORS` dict at the top of
  `rows.py`.
- `Table(..., defaults=...)`, `columns.add(..., default=...)`, and
  `Columns.set_default()` declare insert defaults, applied only by
  `Rows.insert`. `columns.add(..., fill_value=...)` only initializes existing
  rows and is independent of the default. Defaults are deep-copied;
  `get_default` and `get_defaults` return copies, and non-copyable defaults
  raise `TypeError` when set. `remove_default` clears one default;
  `Columns.remove/update` must drop or revalidate the associated default.
  `_insert_defaults(provided)` copies only defaults for omitted columns.
- Inserts and reads use shallow dictionary copies, so mutable cell values may
  be shared. Preserve this behavior.
- `TypeValidator` (in `types.py`) does recursive runtime checks. Plain classes
  follow `isinstance` (so `bool` matches `int`); `Literal` also requires an
  exact type match.
- Export new public symbols from `src/ramtable/__init__.py`; update `__all__`.
  `tests/test_package.py` asserts the exact `__all__` contents and order.

## Documentation

- The site is Zensical. Sources live in `docs/`: `index.md` is the landing
  page, `guide/` holds the installation page and the user guide,
  `reference/` holds the API index, generated class pages, and validation
  rules, and `project/` holds development, releases, changelog,
  contributing, and license.
- `docs/reference/api/*.md` use mkdocstrings to render the package
  docstrings. Change signatures and descriptions in `src/ramtable/`, not in
  generated output.
- `docs/project/changelog.md`, `contributing.md`, and `license.md` include
  the root files through snippets. Edit `CHANGELOG.md`, `CONTRIBUTING.md`,
  and `LICENSE`, not the wrappers.
- `scripts/generate_release_metadata.py` writes the JSON and Markdown files
  under `docs/_data/` and `docs/_generated/`. Both directories are gitignored;
  never commit their contents.
- Add a page to the `nav` list in `zensical.toml`. The strict build fails on
  broken Markdown and the checker validates links, anchors, and assets in the
  built HTML.
- Keep `README.md` short: introduction, installation, one example, and a
  link to the site. Put details in `docs/` and link to the site path.

## Versions and releases

- `pyproject.toml` `project.version` is the only source of truth.
  `ramtable.__version__` comes from installed metadata; never hardcode a
  version in README or docs.
- Branches: `dev → test_pypi → main`. Contribute against `dev`; `test_pypi`
  and `main` are release branches.
- PEP 440 forms: dev `X.Y.ZdevN`, TestPyPI `X.Y.ZrcN` or `X.Y.Z`, PyPI
  stable only. Development versions are never published.
- Do not bump the version unless asked. A release bump also updates
  `CHANGELOG.md`; sections are newest first.
- Commits use Conventional Commits (e.g. `fix:`, `docs:`).
- `tests.yml` runs on pushes to `dev` and PRs to `dev`/`test_pypi`/`main`;
  publish workflows only publish after a PR is merged.
- `docs.yml` builds on PRs to `main` and deploys from `main` on push,
  schedule, and manual dispatch. `docs-notify.yml` dispatches a build from
  `main` when `dev` or `test_pypi` changes `pyproject.toml`; it never checks
  out branch code.

## Local gotchas

- `.pyirc` and `my_test.py` are gitignored local files; never commit them.
- `dist/`, `site/`, `docs/_data/`, and `docs/_generated/` are gitignored.
  `dist/` and `site/` may hold stale artifacts; the generated docs files are
  recreated by the build.
- When behavior changes, update the matching doc: `docs/guide/index.md` for
  workflows, `docs/guide/installation.md` for install steps, the docstrings
  under `src/ramtable/` (rendered in `docs/reference/api/`) for signatures,
  and `docs/reference/types-and-validation.md` for validation rules.
