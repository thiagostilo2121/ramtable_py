"""Tests for the public ``Columns`` schema view."""

import pytest

from ramtable import Table


def test_get_and_get_all_return_the_schema(people_table):
    assert people_table.columns.get("age") is int
    assert people_table.columns.get_all() == {
        "id": int,
        "name": str,
        "age": int,
        "active": bool,
    }


def test_get_all_returns_a_copy(people_table):
    schema = people_table.columns.get_all()
    schema["extra"] = str

    assert "extra" not in people_table.columns
    assert people_table.columns.get_all() == {
        "id": int,
        "name": str,
        "age": int,
        "active": bool,
    }


def test_schema_supports_membership_length_and_repr(people_table):
    assert "age" in people_table.columns
    assert "missing" not in people_table.columns
    assert len(people_table.columns) == 4
    assert "Columns(" in repr(people_table.columns)
    assert "'age': <class 'int'>" in repr(people_table.columns)


def test_get_missing_column_raises_value_error(empty_table):
    with pytest.raises(ValueError, match="does not exist"):
        empty_table.columns.get("missing")


def test_add_column_to_empty_table_without_default(empty_table):
    empty_table.columns.add("score", int)

    assert empty_table.columns.get_all() == {"id": int, "name": str, "score": int}
    assert len(empty_table.rows) == 0


def test_add_column_to_empty_table_does_not_store_an_unused_default():
    table = Table("items", {"id": int})

    table.columns.add("tags", list[str], default=["new"])

    assert table.columns.get("tags") == list[str]
    assert table.rows.get_all() == []


def test_add_column_requires_default_when_rows_exist(people_table):
    with pytest.raises(ValueError, match="default value is required"):
        people_table.columns.add("score", int)

    assert "score" not in people_table.columns
    assert people_table.rows.get_one(0) == {
        "id": 1,
        "name": "Ada",
        "age": 36,
        "active": True,
    }


def test_add_column_initializes_every_existing_row(people_table):
    people_table.columns.add("score", int, default=10)

    assert people_table.columns.get("score") is int
    assert people_table.rows.get_columns("id", "score") == {
        "id": [1, 2, 3],
        "score": [10, 10, 10],
    }


def test_add_column_with_invalid_default_leaves_schema_and_rows_unchanged(
    people_table,
):
    schema_before = people_table.columns.get_all()
    rows_before = people_table.rows.get_all()

    with pytest.raises(TypeError, match="Default value"):
        people_table.columns.add("score", int, default="invalid")

    assert people_table.columns.get_all() == schema_before
    assert people_table.rows.get_all() == rows_before


def test_add_column_deep_copies_mutable_default_per_row():
    table = Table("items", {"id": int})
    table.rows.insert({"id": 1})
    table.rows.insert({"id": 2})
    default = ["new"]

    table.columns.add("tags", list[str], default=default)

    stored = table.rows.get_all()
    stored[0]["tags"].append("changed")

    assert table.rows.get_one(0)["tags"] == ["new", "changed"]
    assert table.rows.get_one(1)["tags"] == ["new"]
    assert default == ["new"]


@pytest.mark.parametrize("name", ["", "   ", None, 1])
def test_add_rejects_invalid_column_names(empty_table, name):
    with pytest.raises(ValueError, match="non-empty strings"):
        empty_table.columns.add(name, int)


def test_add_rejects_duplicate_column_name(empty_table):
    with pytest.raises(ValueError, match="already exists"):
        empty_table.columns.add("id", int)


def test_add_rejects_unsupported_annotation(empty_table):
    with pytest.raises(TypeError, match="Unsupported column type"):
        empty_table.columns.add("bad", list[int, str])


def test_add_appends_columns_in_order(empty_table):
    empty_table.columns.add("score", int)
    empty_table.columns.add("tags", list[str])

    assert list(empty_table.columns.get_all()) == [
        "id",
        "name",
        "score",
        "tags",
    ]


def test_remove_column_updates_schema_and_all_rows(people_table):
    people_table.columns.remove("age")

    assert people_table.columns.get_all() == {
        "id": int,
        "name": str,
        "active": bool,
    }
    assert people_table.rows.get_all() == [
        {"id": 1, "name": "Ada", "active": True},
        {"id": 2, "name": "Linus", "active": False},
        {"id": 3, "name": "Grace", "active": True},
    ]


def test_remove_missing_column_raises_value_error(empty_table):
    with pytest.raises(ValueError, match="does not exist"):
        empty_table.columns.remove("missing")


def test_remove_last_column_is_rejected():
    table = Table("one", {"id": int})

    with pytest.raises(ValueError, match="at least one column"):
        table.columns.remove("id")

    assert table.columns.get_all() == {"id": int}


def test_update_column_type_when_all_values_match(people_table):
    people_table.columns.update("age", int | float)

    assert people_table.columns.get("age") == int | float
    assert people_table.rows.get_column("age") == [36, 28, 45]


def test_update_column_type_does_not_convert_values(people_table):
    people_table.columns.update("id", object)

    assert people_table.columns.get("id") is object
    assert people_table.rows.get_column("id") == [1, 2, 3]
    assert all(isinstance(value, int) for value in people_table.rows.get_column("id"))


def test_update_column_type_is_atomic_when_a_value_does_not_match(people_table):
    schema_before = people_table.columns.get_all()

    with pytest.raises(TypeError, match="does not match"):
        people_table.columns.update("id", str)

    assert people_table.columns.get_all() == schema_before
    assert people_table.rows.get_column("id") == [1, 2, 3]


def test_update_column_type_rejects_unsupported_annotation(empty_table):
    with pytest.raises(TypeError, match="Unsupported column type"):
        empty_table.columns.update("id", list[int, str])


def test_update_missing_column_raises_value_error(empty_table):
    with pytest.raises(ValueError, match="does not exist"):
        empty_table.columns.update("missing", int)
