# Changelog

Notable changes to RAMTable are documented in this file. The history starts
with the project's first version.

## [0.3.0] - In preparation

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

