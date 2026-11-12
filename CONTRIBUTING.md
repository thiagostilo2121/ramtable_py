# Contributing to RAMTable

Thank you for considering a contribution to RAMTable. Bug fixes,
documentation improvements, tests, refactorings, performance work, and
approved new features are all welcome. This guide explains how the project is
maintained and how to prepare a contribution that is easy to review.

## Contents

- [Ways to contribute](#ways-to-contribute)
- [AI-assisted contributions](#ai-assisted-contributions)
- [New features require approval](#new-features-require-approval)
- [Maintenance and review expectations](#maintenance-and-review-expectations)
- [Branch workflow](#branch-workflow)
- [Development setup](#development-setup)
- [Checks, testing, and supported Python versions](#checks-testing-and-supported-python-versions)
- [Code style and documentation](#code-style-and-documentation)
- [Changelog and versioning](#changelog-and-versioning)
- [Pull request guidelines](#pull-request-guidelines)
- [Reporting bugs](#reporting-bugs)
- [License](#license)

## Ways to contribute

Contributions of all sizes are appreciated:

- bug fixes;
- documentation improvements;
- tests and test coverage;
- code refactoring;
- performance improvements;
- new features, after prior approval;
- other improvements that fit the project's goals.

## AI-assisted contributions

The repository includes an [`AGENTS.md`](AGENTS.md) file for contributors who
use AI coding assistants or other AI tools as part of their workflow. It
collects the project's setup commands, architecture notes, conventions, and
release rules so these tools can work with accurate context.

`AGENTS.md` is available in the repository for anyone to use. It is optional
guidance, not a replacement for this guide: contributors remain responsible
for reviewing AI-generated changes, running the checks, keeping changes
focused, and following the approval and pull request rules described here. If
project conventions or commands change, update `AGENTS.md` along with the
related documentation.

## New features require approval

To keep the project's direction coherent and avoid work that may not fit its
goals, **new features must be approved before implementation**.

Before writing code for a new feature:

1. Open a GitHub Issue describing the proposed functionality.
2. Explain the problem it solves and why it would be useful.
3. Wait for a maintainer to approve the proposal.

Pull requests that introduce unapproved features may be closed without being
merged. If you are unsure whether your idea counts as a new feature, open an
Issue and ask before starting.

Small fixes, documentation updates, and refactorings that do not change
behavior do not need prior approval.

## Maintenance and review expectations

**RAMTable is currently maintained by a single developer.** There is no
dedicated team handling Issues or reviewing pull requests.

As a result:

- Issue responses may take some time.
- Pull request reviews may be delayed.
- A contribution may remain pending for a while before receiving feedback.
- Immediate responses and merges should not be expected.
- The maintainer reviews contributions as time and availability allow.

This does not mean contributions are unwelcome. Every report and pull request
is appreciated, and a polite follow-up after a reasonable waiting period is
fine. Clear, focused contributions are easier to review and more likely to
move forward.

## Branch workflow

The development branch is **`dev`**. Open contributions as pull requests
against `dev`.

Maintainers promote releases through the permanent branches:

```text
dev → test_pypi → main
```

`test_pypi` and `main` are release branches. Unless a maintainer asks you
otherwise, do not open contribution pull requests against them.

Create a branch from an up-to-date `dev` and use one of these prefixes:

| Prefix | Purpose | Example |
|---|---|---|
| `feat/` | New features approved through an Issue | `feat/bulk-insert` |
| `fix/` | Bug fixes | `fix/column-validation` |
| `docs/` | Documentation changes | `docs/api-reference` |
| `refactor/` | Code refactoring | `refactor/row-storage` |
| `test/` | Test-related changes | `test/column-edge-cases` |

For example:

```bash
git switch dev
git pull upstream dev
git switch -c fix/column-validation
```

These commands assume the `upstream` remote added in
[Development setup](#development-setup).

## Development setup

RAMTable requires **Python 3.11 or later**.

1. Fork the repository on GitHub.
2. Clone your fork and add the upstream repository:

   ```bash
   git clone https://github.com/<your-user>/ramtable_py.git
   cd ramtable_py
   git remote add upstream https://github.com/thiagostilo2121/ramtable_py.git
   ```

3. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows, use `python` instead of `python3` and activate with:

   ```powershell
   .venv\Scripts\activate
   ```

4. Install the project in editable mode with the test dependencies:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install --editable ".[dev]"
   ```

RAMTable has no runtime dependencies. The `dev` extra installs `pytest` and
`pytest-cov`. If you need to build distributions, install the build tools
separately:

```bash
python -m pip install build twine
```

## Checks, testing, and supported Python versions

The test suite lives in `tests/` and uses pytest. No linter, formatter, or
static type checker is configured.

Run the suite from the repository root:

```bash
python -m pytest
```

To include coverage information:

```bash
python -m pytest --cov=ramtable --cov-report=term-missing
```

The CI workflow installs the package and its development dependencies, runs
the test suite, byte-compiles the package, and checks the public imports. You
can run the non-test checks locally:

```bash
python -m compileall -q src/ramtable
python -c "from ramtable import Columns, Rows, Table"
```

If you build distributions, validate them with:

```bash
python -m build
python -m twine check dist/*
```

GitHub Actions runs these checks on Python **3.11, 3.12, 3.13, 3.14, and
3.15** for pushes to `dev` and for pull requests targeting `dev`, `test_pypi`,
and `main`. Pull requests targeting `test_pypi` and `main` also run the
release validation and build; publication happens only after a pull request is
merged. Keep every change compatible with all supported versions.

### What to test

- **Bug fixes:** include a regression test that fails before the fix and
  passes afterwards.
- **New functionality:** include tests with the implementation. Tests should
  verify observable behavior and the resulting table state.
- **Documentation and refactorings:** confirm that the existing examples,
  tests, and public imports still work.

Do not claim that a check is passing if you did not run it.

## Code style and documentation

Follow the style and structure already used in `src/ramtable`:

- use four-space indentation and keep lines close to 79 characters;
- add type hints to functions and methods;
- write docstrings in the existing style, with `Args`, `Returns`, and
  `Raises` sections where applicable;
- raise standard exceptions with clear messages, such as `ValueError`,
  `TypeError`, or `IndexError`;
- preserve the library's validate-then-write behavior: validate a request
  completely before modifying stored rows;
- keep the public API consistent, and expose new public symbols through
  `src/ramtable/__init__.py` and `__all__`;
- avoid adding runtime dependencies unless they are discussed and approved in
  an Issue;
- keep changes focused on the problem described in the Issue or pull request.

When behavior changes, update the relevant documentation in `docs/`:

- `docs/guide.md` for user-facing workflows;
- `docs/api.md` for signatures, arguments, returns, and exceptions;
- `docs/types-and-validation.md` for validation rules.

The repository history uses Conventional Commits-style messages, such as
`fix: ...`, `docs: ...`, and `feat: ...`. Following that style is appreciated,
but clear and descriptive commit messages matter most.

## Changelog and versioning

`CHANGELOG.md` records notable changes under version headings, with sections
such as `Added`, `Changed`, and `Fixed`. User-visible changes should be
reflected there when appropriate. Internal refactorings and trivial changes do
not need an entry. If you are unsure, mention the change in your pull request
and ask.

Do not modify `project.version` in `pyproject.toml`, create release headings,
or hardcode the current version in the README or documentation.
`pyproject.toml` is the single source of truth for the version, and version
bumps are part of the maintainer's release process.

## Pull request guidelines

Pull requests should:

- have a clear, descriptive title;
- explain what changed and why;
- reference the related Issue when one exists;
- include tests for relevant changes, following the guidance above;
- update documentation when behavior or the public API changes;
- avoid unrelated changes;
- stay focused and reasonably small whenever possible.

For a new feature, link the Issue where the feature was approved. Pull
requests without that approval may be closed.

Opening a pull request does not guarantee acceptance or an immediate review.
The maintainer may request changes, ask for the branch to be updated, or
decide that a contribution does not fit the project's direction.

Before opening a pull request:

```bash
git fetch upstream
git switch dev
git pull upstream dev
git switch your-branch-name
git rebase upstream/dev
```

Then run the checks described above and make sure the diff contains only the
intended changes.

## Reporting bugs

When reporting a bug, include:

- the RAMTable version:

  ```bash
  python -c "import ramtable; print(ramtable.__version__)"
  ```

- your Python version and operating system;
- a minimal, reproducible example;
- the expected result and the actual result;
- the complete traceback, if one was raised.

Search existing Issues first to avoid duplicates.

## License

RAMTable is released under the MIT License. See [LICENSE](LICENSE) for the
full text. By contributing, you agree that your contributions may be
distributed under the same license.
