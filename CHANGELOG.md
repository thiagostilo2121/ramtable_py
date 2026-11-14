# Changelog

Notable changes to RAMTable are documented in this file. The history starts
with the project's first version.

## [0.5.0rc0]

Completes insert-default management after table creation and adds the
documentation site.

### Added

- `Columns.add()` accepts `default` for future inserts while `fill_value`
  keeps initializing existing rows. The two values are independent, and a
  fill value is still required when rows exist.
- `Columns.set_default()` sets or replaces a column's insert default, and
  `Columns.remove_default()` clears it.
- `Columns.get_defaults()` returns deep copies of every insert default.
- Documentation site built with Zensical, with an installation page, user
  guide, API reference generated from docstrings, and project pages.
- Executable documentation examples, also run against the built wheel in
  continuous integration.
- Releases page with branch and package-index metadata generated during the
  documentation build.
- Documentation workflows that build pull requests to `main`, deploy from
  `main`, and refresh the site when a release branch changes its version.

### Changed

- `Columns.get_default()` and `get_defaults()` raise a descriptive
  `TypeError` when deep-copying fails.
- `Columns.add()` raises a descriptive `TypeError` when a fill value cannot
  be deep-copied.
- `Rows.insert()` copies defaults only for columns the row omits.
- `Table.clear()` and `Rows.clear()` now document that they preserve insert
  defaults.
- `README.md` covers installation, a short example, and a link to the site;
  the details moved under `docs/`.
- `AGENTS.md` and `CONTRIBUTING.md` document the documentation paths, build
  commands, and generated files.

## [0.4.1]

Reviews the README and documentation, corrects guide examples, and updates
stale workflow comments. No behavior changes.

### Changed

- Rewrote `README.md` and the documents under `docs/` to remove filler,
  passive constructions, and formulaic phrasing. Examples, signatures, and
  exception lists stay unchanged.
- Corrected the user guide's remove, schema, and copy examples so they match
  the table state and run in sequence.
- Removed the duplicate project status section from `README.md`.
- `docs/development.md` no longer pins an output block for `my_test.py`. The
  local example changes independently of the documentation.
- Corrected the test-suite comments in the PyPI and TestPyPI publish
  workflows to point at `tests.yml`.

## [0.4.0]

Adds insert defaults for table columns, an automated test suite, and
continuous integration coverage. Also applies linting fixes across the
package and test suite.

### Added

- Optional `defaults` mapping for `Table` so inserted rows can omit columns
  with declared defaults. Defaults are validated, deep-copied for isolation,
  and available through `Columns.get_default()`.
- Insert defaults must support `deepcopy`; a non-copyable default raises
  `TypeError` during table creation with the affected column name.
- Pytest suite under `tests/` covering `Table`, `Rows`, `Columns`, filtering,
  mutations, `TypeValidator`, integration workflows, and edge cases.
- `dev` optional dependency group with `pytest` and `pytest-cov`.
- Coverage reporting for the test suite.

### Changed

- `Columns.add()` now uses `fill_value` instead of `default` for the value
  applied to existing rows. It does not create an insert default.
- GitHub Actions now installs the development dependencies and runs the test
  suite on Python 3.11 through 3.15, in addition to byte-compilation and
  import checks.
- Development and contribution documentation now describe the test suite and
  its commands.
- Reformatted source and test code to keep lines within the project's
  79-column style.
- Simplified the fill-value validation branch in `Columns.add` without
  changing behavior.

## [0.3.3]

Adds contribution guidelines for the project.

### Added

- `CONTRIBUTING.md` covering contribution scope, the prior-approval policy
  for new features, single-maintainer review expectations, branch naming,
  development setup, testing expectations, and pull request guidelines.

### Changed

- `rows.py` changed `indices` to `indexes` in `get()` methods.

## [0.3.2]

Raises the minimum supported Python version, expands the tested versions,
and centralizes the package version.

### Added

- `ramtable.__version__` exposes the installed distribution version, read
  from package metadata.

### Changed

- Python 3.11 or later is now required; support for Python 3.10 was removed.
- Added Python 3.14 and 3.15 to the test matrix and package classifiers.
- `pyproject.toml` is the single source of truth for the version; the README
  uses a dynamic PyPI badge instead of a hardcoded number.

## [0.3.1]

Publishes RAMTable to the official PyPI index alongside TestPyPI.

### Added

- Stable releases are now published to PyPI under the name `ramtable`.
- Branch-based release flow (`dev` → `test_pypi` → `main`) with PEP 440
  version validation in GitHub Actions.
- Trusted Publishing with OIDC for both PyPI and TestPyPI; no API tokens are
  stored in the repository.

### Changed

- Installation documentation covers stable releases from PyPI and
  pre-releases from TestPyPI.

## [0.3.0]

Adds declarative filtering and shares one condition engine across filtering,
updating, and deleting rows.

### Added

- `Rows.filter(where)` returns the rows that match a set of conditions.
- `Rows.delete(where)` removes every matching row and returns the number
  deleted.
- Flexible conditions in `where`: comparison operators (`==`, `!=`, `>`,
  `>=`, `<`, `<=`), membership (`in`, `not_in`), string and container
  matching (`contains`, `startswith`, `endswith`), and callable predicates.
- Documentation for filtering, deletion, and the shared condition format.

### Changed

- `Rows.update(where, values)` now accepts the same flexible conditions;
  plain values still mean equality.
- A dictionary in `where` is now interpreted as an operator specification;
  to compare a column against a dictionary value, use `{"==": value}`.
- `pyproject.toml` and the README now report version `0.3.0`.

## [0.2.0]

This version prepares complete project documentation and a more useful
onboarding experience for users installing RAMTable from TestPyPI.

### Added

- Expanded README covering the project's purpose, status, installation, quick
  start, features, and documentation links.
- Detailed user guide, API reference, type-validation guide, and development
  guide.
- Project changelog.

### Changed

- Updated the `pyproject.toml` project version to `0.2.0`.

## [0.1.1]

### Fixed

- Corrected the `pyproject.toml` packaging configuration to include the
  package located at `src/ramtable` when building distributions.

## [0.1.0]

### Added

- First RAMTable version: in-memory tables with a typed column schema and
  basic row operations.
- Runtime validation of row structure and value types.
- Publish to Test PyPi.

