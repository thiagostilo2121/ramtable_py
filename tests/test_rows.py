"""Tests for the public ``Rows`` view."""

import pytest

from ramtable import Table


def test_insert_appends_a_valid_row(empty_table):
    empty_table.rows.insert({"id": 1, "name": "Ada"})

    assert len(empty_table.rows) == 1
    assert empty_table.rows.get_one(0) == {"id": 1, "name": "Ada"}


def test_insert_stores_a_shallow_copy_of_the_input_dictionary():
    table = Table("items", {"id": int, "tags": list[str]})
    row = {"id": 1, "tags": ["original"]}

    table.rows.insert(row)
    row["id"] = 99
    row["tags"].append("changed")

    stored = table.rows.get_one(0)
    assert stored["id"] == 1
    assert stored["tags"] == ["original", "changed"]


@pytest.mark.parametrize(
    "row",
    [
        {"id": 1},
        {"id": 1, "name": "Ada", "extra": True},
        {"name": "Ada"},
        {},
    ],
)
def test_insert_rejects_rows_with_the_wrong_shape(empty_table, row):
    with pytest.raises(ValueError, match="Invalid row structure"):
        empty_table.rows.insert(row)

    assert len(empty_table.rows) == 0


@pytest.mark.parametrize("row", [None, [], "id", 1])
def test_insert_rejects_non_dictionary_rows(empty_table, row):
    with pytest.raises(TypeError, match="dictionary"):
        empty_table.rows.insert(row)


def test_insert_rejects_invalid_value_types(empty_table):
    with pytest.raises(TypeError, match="Invalid value"):
        empty_table.rows.insert({"id": "1", "name": "Ada"})

    assert len(empty_table.rows) == 0


def test_insert_uses_python_isinstance_semantics_for_bool_and_int(empty_table):
    empty_table.rows.insert({"id": True, "name": "Ada"})

    assert empty_table.rows.get_one(0) == {"id": True, "name": "Ada"}


def test_get_without_arguments_returns_every_row_in_order(people_table):
    assert people_table.rows.get() == people_table.rows.get_all()


def test_get_accepts_positive_negative_and_repeated_indexes(people_table):
    selected = people_table.rows.get(0, -1, 0)

    assert [row["id"] for row in selected] == [1, 3, 1]


@pytest.mark.parametrize("index", [True, False, 1.0, "0", None])
def test_get_rejects_non_integer_indexes(people_table, index):
    with pytest.raises(TypeError, match="indexes must be integers"):
        people_table.rows.get(index)


@pytest.mark.parametrize("index", [3, -4])
def test_get_rejects_out_of_range_indexes(people_table, index):
    with pytest.raises(IndexError, match="out of range"):
        people_table.rows.get(index)


def test_get_returns_new_row_dictionaries(people_table):
    row = people_table.rows.get(0)[0]
    row["name"] = "Changed"

    assert people_table.rows.get_one(0)["name"] == "Ada"


def test_get_one_supports_negative_indexes(people_table):
    assert people_table.rows.get_one(-1)["name"] == "Grace"


@pytest.mark.parametrize("index", [True, False, 1.0, "0", None])
def test_get_one_rejects_non_integer_indexes(people_table, index):
    with pytest.raises(TypeError, match="index must be an integer"):
        people_table.rows.get_one(index)


@pytest.mark.parametrize("index", [3, -4])
def test_get_one_rejects_out_of_range_indexes(people_table, index):
    with pytest.raises(IndexError, match="out of range"):
        people_table.rows.get_one(index)


def test_get_all_returns_new_row_dictionaries(people_table):
    rows = people_table.rows.get_all()
    rows[0]["name"] = "Changed"

    assert people_table.rows.get_one(0)["name"] == "Ada"


def test_get_columns_returns_the_requested_columns_in_order(people_table):
    columns = people_table.rows.get_columns("name", "id")

    assert columns == {
        "name": ["Ada", "Linus", "Grace"],
        "id": [1, 2, 3],
    }
    assert list(columns) == ["name", "id"]


def test_get_columns_without_arguments_returns_every_column(people_table):
    assert people_table.rows.get_columns() == {
        "id": [1, 2, 3],
        "name": ["Ada", "Linus", "Grace"],
        "age": [36, 28, 45],
        "active": [True, False, True],
    }


def test_get_columns_allows_duplicate_names(people_table):
    columns = people_table.rows.get_columns("id", "id")

    assert columns == {"id": [1, 2, 3]}


def test_get_columns_does_not_copy_cell_values():
    table = Table("items", {"id": int, "tags": list[str]})
    table.rows.insert({"id": 1, "tags": ["original"]})

    columns = table.rows.get_columns("tags")
    columns["tags"][0].append("changed")

    assert table.rows.get_one(0)["tags"] == ["original", "changed"]


def test_get_columns_rejects_missing_names(people_table):
    with pytest.raises(ValueError, match="does not exist"):
        people_table.rows.get_columns("id", "missing")


def test_get_column_returns_values_without_copying_them():
    table = Table("items", {"id": int, "tags": list[str]})
    table.rows.insert({"id": 1, "tags": ["original"]})

    values = table.rows.get_column("tags")
    values[0].append("changed")

    assert table.rows.get_one(0)["tags"] == ["original", "changed"]


def test_get_column_rejects_missing_names(people_table):
    with pytest.raises(ValueError, match="does not exist"):
        people_table.rows.get_column("missing")


def test_iteration_yields_new_row_dictionaries(people_table):
    iterator = iter(people_table.rows)
    first = next(iterator)
    first["name"] = "Changed"

    assert people_table.rows.get_one(0)["name"] == "Ada"


def test_len_and_repr_track_the_number_of_rows(people_table):
    assert len(people_table.rows) == 3
    assert repr(people_table.rows) == "Rows(count=3)"


def test_clear_removes_rows_and_preserves_schema(people_table):
    people_table.rows.clear()

    assert len(people_table.rows) == 0
    assert people_table.rows.get_all() == []
    assert people_table.columns.get_all() == {
        "id": int,
        "name": str,
        "age": int,
        "active": bool,
    }


def test_remove_deletes_the_first_equal_row():
    table = Table("items", {"id": int, "name": str})
    table.rows.insert({"id": 1, "name": "Ada"})
    table.rows.insert({"id": 1, "name": "Ada"})
    table.rows.insert({"id": 2, "name": "Linus"})

    table.rows.remove({"id": 1, "name": "Ada"})

    assert table.rows.get_all() == [
        {"id": 1, "name": "Ada"},
        {"id": 2, "name": "Linus"},
    ]


def test_remove_rejects_a_row_that_does_not_exist(people_table):
    row = {"id": 99, "name": "Nobody", "age": 1, "active": False}

    with pytest.raises(ValueError, match="does not exist"):
        people_table.rows.remove(row)

    assert len(people_table.rows) == 3


def test_remove_rejects_an_invalid_shape(people_table):
    with pytest.raises(ValueError, match="Invalid row structure"):
        people_table.rows.remove({"id": 1})

    assert len(people_table.rows) == 3


def test_remove_rejects_an_invalid_value_type(people_table):
    row = {"id": "1", "name": "Ada", "age": 36, "active": True}

    with pytest.raises(TypeError, match="Invalid value"):
        people_table.rows.remove(row)

    assert len(people_table.rows) == 3
