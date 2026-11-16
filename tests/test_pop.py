"""Tests for removing a row by position."""

import pytest

from ramtable import Table


def test_pop_removes_and_returns_the_row_at_an_index(people_table):
    removed = people_table.rows.pop(1)

    assert removed == {
        "id": 2,
        "name": "Linus",
        "age": 28,
        "active": False,
    }
    assert people_table.rows.get_all() == [
        {"id": 1, "name": "Ada", "age": 36, "active": True},
        {"id": 3, "name": "Grace", "age": 45, "active": True},
    ]


def test_pop_supports_negative_indexes(people_table):
    removed = people_table.rows.pop(-1)

    assert removed["name"] == "Grace"
    assert [row["id"] for row in people_table.rows.get_all()] == [1, 2]


@pytest.mark.parametrize("index", [True, False, 1.0, "0", None])
def test_pop_rejects_non_integer_indexes(people_table, index):
    with pytest.raises(TypeError, match="index must be an integer"):
        people_table.rows.pop(index)

    assert len(people_table.rows) == 3


@pytest.mark.parametrize("index", [3, -4])
def test_pop_rejects_out_of_range_indexes(people_table, index):
    with pytest.raises(IndexError, match="out of range"):
        people_table.rows.pop(index)

    assert len(people_table.rows) == 3


def test_pop_can_empty_a_table():
    table = Table("items", {"id": int})
    table.rows.insert({"id": 1})

    assert table.rows.pop(0) == {"id": 1}
    assert table.rows.get_all() == []

    with pytest.raises(IndexError, match="out of range"):
        table.rows.pop(0)
