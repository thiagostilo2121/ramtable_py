"""Smoke tests for the public package surface."""

import ramtable
from ramtable import Columns, Rows, Table


def test_public_classes_are_exported():
    assert ramtable.__all__ == [
        "__version__",
        "Columns",
        "Rows",
        "Table",
    ]
    assert ramtable.Columns is Columns
    assert ramtable.Rows is Rows
    assert ramtable.Table is Table


def test_public_version_is_a_non_empty_string():
    assert isinstance(ramtable.__version__, str)
    assert ramtable.__version__


def test_public_classes_can_be_used_from_the_package_namespace():
    table = Table("items", {"id": int})

    assert isinstance(table.columns, Columns)
    assert isinstance(table.rows, Rows)
    table.rows.insert({"id": 1})
    assert table.rows.get_one(0) == {"id": 1}
