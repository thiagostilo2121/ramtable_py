"""Tests for the public ``Table`` container."""

import pytest

from ramtable import Columns, Rows, Table


def test_table_initializes_with_name_schema_and_no_rows():
    table = Table("people", {"id": int, "name": str})

    assert table.name == "people"
    assert table.columns.get_all() == {"id": int, "name": str}
    assert len(table.columns) == 2
    assert len(table.rows) == 0
    assert len(table) == 0


def test_table_exposes_coordinated_rows_and_columns():
    table = Table("people", {"id": int, "name": str})

    assert isinstance(table.rows, Rows)
    assert isinstance(table.columns, Columns)

    table.rows.insert({"id": 1, "name": "Ada"})

    assert table.rows.get_one(0) == {"id": 1, "name": "Ada"}
    assert table.columns.get_all() == {"id": int, "name": str}
    assert len(table) == 1


def test_table_preserves_the_exact_name():
    table = Table("  people  ", {"id": int})

    assert table.name == "  people  "


def test_table_copies_the_initial_schema_dictionary():
    schema = {"id": int}
    table = Table("people", schema)

    schema["name"] = str

    assert table.columns.get_all() == {"id": int}


def test_table_clear_removes_rows_and_preserves_schema(people_table):
    people_table.clear()

    assert len(people_table) == 0
    assert people_table.rows.get_all() == []
    assert people_table.columns.get_all() == {
        "id": int,
        "name": str,
        "age": int,
        "active": bool,
    }


def test_table_len_tracks_row_mutations(people_table):
    assert len(people_table) == 3

    people_table.rows.delete({"id": 2})
    assert len(people_table) == 2

    people_table.rows.clear()
    assert len(people_table) == 0


def test_table_repr_contains_name_columns_and_row_count(people_table):
    representation = repr(people_table)

    assert "Table(" in representation
    assert "name='people'" in representation
    assert "columns=" in representation
    assert "'id'" in representation
    assert "rows=3" in representation


@pytest.mark.parametrize("name", ["", "   ", None, 1, [], {}])
def test_table_rejects_invalid_names(name):
    with pytest.raises(ValueError):
        Table(name, {"id": int})


@pytest.mark.parametrize("columns", [None, [], {}, "id", 1])
def test_table_rejects_invalid_schemas(columns):
    with pytest.raises(ValueError):
        Table("people", columns)


@pytest.mark.parametrize("name", ["", "   ", None, 1])
def test_table_rejects_invalid_column_names(name):
    with pytest.raises(ValueError):
        Table("people", {name: int})


@pytest.mark.parametrize(
    "annotation",
    [
        list[int, str],
        dict[str],
        tuple[int, str, ...],
        object(),
    ],
)
def test_table_rejects_unsupported_annotations(annotation):
    with pytest.raises(TypeError):
        Table("people", {"value": annotation})
