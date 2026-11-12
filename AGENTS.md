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

## Architecture

- `Table` creates one `storage` list and passes it to both `Columns` and
  `Rows`. Schema changes and row operations act on that same list.
- Keep validate-then-write semantics: `Columns.add/remove/update` and
  `Rows.update` must fully validate before mutating any row.
- `Rows._filter` is the single condition engine behind `filter`, `update`,
  and `delete`; operators live in the `_FILTER_OPERATORS` dict at the top of
  `rows.py`.
- Inserts and reads use shallow dictionary copies, so mutable cell values may
  be shared. Preserve this behavior.
- `TypeValidator` (in `types.py`) does recursive runtime checks. Plain classes
  follow `isinstance` (so `bool` matches `int`); `Literal` also requires an
  exact type match.
- Export new public symbols from `src/ramtable/__init__.py`; update `__all__`.
  `tests/test_package.py` asserts the exact `__all__` contents and order.

## Versions and releases

- `pyproject.toml` `project.version` is the only source of truth.
  `ramtable.__version__` comes from installed metadata; never hardcode a
  version in README or docs.
- Branches: `dev → test_pypi → main`. Contribute against `dev`; `test_pypi`
  and `main` are release branches.
- PEP 440 forms: dev `X.Y.Z.devN`, TestPyPI `X.Y.ZrcN` or `X.Y.Z`, PyPI
  stable only. Development versions are never published.
- Do not bump the version unless asked. A release bump also updates
  `CHANGELOG.md`; sections are newest first.
- Commits use Conventional Commits (e.g. `fix:`, `docs:`).
- `tests.yml` runs on pushes to `dev` and PRs to `dev`/`test_pypi`/`main`;
  publish workflows only publish after a PR is merged.

## Local gotchas

- `.pyirc` and `my_test.py` are gitignored local files; never commit them.
- `dist/` is gitignored and may contain stale artifacts.
- When behavior changes, update the matching doc: `docs/guide.md` for
  workflows, `docs/api.md` for signatures, `docs/types-and-validation.md`
  for validation rules.
