# Releases

RAMTable publishes through TestPyPI before PyPI. This page records the
version policy and the versions each branch and package index report.

## Version policy

| Branch | Version form | Example | Published to |
|---|---|---|---|
| `dev` | `X.Y.ZdevN` | `0.4.0dev0` | nothing |
| `test_pypi` | `X.Y.ZrcN` or `X.Y.Z` | `0.4.0rc0`, `0.4.0` | TestPyPI |
| `main` | `X.Y.Z` | `0.4.0` | PyPI |

`MAJOR.MINOR.PATCH` follows semantic versioning:

- `PATCH` for compatible fixes;
- `MINOR` for compatible functionality;
- `MAJOR` for breaking API or behavior changes.

`pyproject.toml` holds the current version. Development versions are never
published. TestPyPI accepts release candidates and stable versions; PyPI
accepts stable versions only.

## Current state

The documentation build regenerates this section. Branch versions come from
Git. Package versions come from the PyPI and TestPyPI JSON APIs. A failed
request labels the data as unavailable and does not stop the build.

--8<-- "docs/_generated/release-metadata.md"
