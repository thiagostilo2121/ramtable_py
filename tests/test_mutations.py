"""Tests for row updates, deletions, and mutation safety."""

import pytest

from ramtable import Table


def test_update_changes_one_matching_row(people_table):
    updated = people_table.rows.update(
        where={"id": 1},
        values={"name": "Ada Lovelace"},
    )

    assert updated == 1
    assert people_table.rows.get_one(0)["name"] == "Ada Lovelace"
    assert people_table.rows.get_one(1)["name"] == "Linus"
    assert people_table.rows.get_one(2)["name"] == "Grace"


def test_update_changes_every_matching_row(people_table):
    updated = people_table.rows.update(
        where={"active": True},
        values={"active": False},
    )

    assert updated == 2
    assert people_table.rows.get_column("active") == [False, False, False]


def test_update_applies_multiple_values(people_table):
    updated = people_table.rows.update(
        where={"id": 2},
        values={"name": "Linus Torvalds", "age": 29, "active": True},
    )

    assert updated == 1
    assert people_table.rows.get_one(1) == {
        "id": 2,
        "name": "Linus Torvalds",
        "age": 29,
        "active": True,
    }


def test_update_returns_zero_when_nothing_matches(people_table):
    updated = people_table.rows.update(
        where={"id": 99},
        values={"name": "Nobody"},
    )

    assert updated == 0
    assert people_table.rows.get_column("name") == ["Ada", "Linus", "Grace"]


def test_update_supports_callable_conditions(people_table):
    updated = people_table.rows.update(
        where={"age": lambda age: age >= 40},
        values={"active": False},
    )

    assert updated == 1
    assert people_table.rows.get_one(2)["active"] is False


def test_update_supports_operator_conditions(people_table):
    updated = people_table.rows.update(
        where={"age": {">": 30}},
        values={"active": False},
    )

    assert updated == 2
    assert people_table.rows.get_column("active") == [False, False, False]


def test_update_does_not_type_check_condition_values(people_table):
    updated = people_table.rows.update(
        where={"age": "36"},
        values={"active": False},
    )

    assert updated == 0
    assert people_table.rows.get_column("active") == [True, False, True]


def test_update_with_invalid_value_leaves_every_row_unchanged(people_table):
    before = people_table.rows.get_all()

    with pytest.raises(TypeError, match="Invalid value"):
        people_table.rows.update(
            where={"active": True},
            values={"age": "invalid"},
        )

    assert people_table.rows.get_all() == before


def test_update_with_invalid_filter_leaves_every_row_unchanged(people_table):
    before = people_table.rows.get_all()

    with pytest.raises(ValueError, match="does not exist"):
        people_table.rows.update(
            where={"missing": 1},
            values={"active": False},
        )

    assert people_table.rows.get_all() == before


def test_update_with_callable_failure_leaves_every_row_unchanged(people_table):
    before = people_table.rows.get_all()

    def fail(value):
        raise RuntimeError("cannot evaluate")

    with pytest.raises(RuntimeError, match="cannot evaluate"):
        people_table.rows.update(
            where={"age": fail},
            values={"active": False},
        )

    assert people_table.rows.get_all() == before


@pytest.mark.parametrize("values", [None, [], "", 0, {}])
def test_update_rejects_invalid_values_containers(people_table, values):
    with pytest.raises(ValueError, match="non-empty dictionary"):
        people_table.rows.update(where={"id": 1}, values=values)


def test_update_rejects_missing_value_columns(people_table):
    with pytest.raises(ValueError, match="does not exist"):
        people_table.rows.update(
            where={"id": 1},
            values={"missing": "value"},
        )


@pytest.mark.parametrize("where", [None, [], "", 0, {}])
def test_update_rejects_invalid_condition_containers(people_table, where):
    with pytest.raises(ValueError, match="non-empty dictionary"):
        people_table.rows.update(where=where, values={"active": False})


def test_update_rejects_unknown_filter_operators(people_table):
    with pytest.raises(ValueError, match="Unknown filter operator"):
        people_table.rows.update(
            where={"age": {"<>": 1}},
            values={"active": False},
        )


def test_update_on_empty_table_returns_zero(empty_table):
    updated = empty_table.rows.update(
        where={"id": 1},
        values={"name": "Ada"},
    )

    assert updated == 0
    assert empty_table.rows.get_all() == []


def test_delete_removes_matching_rows_and_returns_the_count(people_table):
    deleted = people_table.rows.delete({"active": True})

    assert deleted == 2
    assert people_table.rows.get_all() == [
        {"id": 2, "name": "Linus", "age": 28, "active": False},
    ]


def test_delete_returns_zero_when_nothing_matches(people_table):
    deleted = people_table.rows.delete({"id": 99})

    assert deleted == 0
    assert len(people_table.rows) == 3


def test_delete_supports_multiple_conditions(people_table):
    deleted = people_table.rows.delete({"active": True, "age": {">": 40}})

    assert deleted == 1
    assert people_table.rows.get_column("id") == [1, 2]


def test_delete_supports_callable_conditions(people_table):
    deleted = people_table.rows.delete({"name": lambda name: name.startswith("L")})

    assert deleted == 1
    assert people_table.rows.get_column("id") == [1, 3]


def test_delete_preserves_the_order_of_remaining_rows(people_table):
    people_table.rows.delete({"id": 2})

    assert people_table.rows.get_column("id") == [1, 3]


def test_delete_with_invalid_filter_leaves_every_row_unchanged(people_table):
    before = people_table.rows.get_all()

    with pytest.raises(ValueError, match="does not exist"):
        people_table.rows.delete({"missing": 1})

    assert people_table.rows.get_all() == before


def test_delete_with_unknown_operator_leaves_every_row_unchanged(people_table):
    before = people_table.rows.get_all()

    with pytest.raises(ValueError, match="Unknown filter operator"):
        people_table.rows.delete({"age": {"<>": 1}})

    assert people_table.rows.get_all() == before


def test_delete_all_rows_preserves_the_schema(people_table):
    deleted = people_table.rows.delete({"id": {">=": 0}})

    assert deleted == 3
    assert people_table.rows.get_all() == []
    assert people_table.columns.get_all() == {
        "id": int,
        "name": str,
        "age": int,
        "active": bool,
    }


def test_delete_on_empty_table_returns_zero(empty_table):
    assert empty_table.rows.delete({"id": 1}) == 0


def test_delete_removes_all_equal_rows_unlike_remove():
    table = Table("items", {"id": int, "name": str})
    table.rows.insert({"id": 1, "name": "Ada"})
    table.rows.insert({"id": 1, "name": "Ada"})
    table.rows.insert({"id": 2, "name": "Linus"})

    deleted = table.rows.delete({"id": 1, "name": "Ada"})

    assert deleted == 2
    assert table.rows.get_all() == [{"id": 2, "name": "Linus"}]
