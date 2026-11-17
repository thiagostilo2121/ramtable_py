"""Tests for atomic bulk row insertion."""

import pytest

from ramtable import Table


def test_insert_many_appends_rows_and_returns_the_count(empty_table):
    count = empty_table.rows.insert_many(
        [
            {"id": 1, "name": "Ada"},
            {"id": 2, "name": "Linus"},
        ]
    )

    assert count == 2
    assert empty_table.rows.get_all() == [
        {"id": 1, "name": "Ada"},
        {"id": 2, "name": "Linus"},
    ]


def test_insert_many_accepts_any_iterable(empty_table):
    rows = (
        {"id": index, "name": str(index)}
        for index in range(3)
    )

    assert empty_table.rows.insert_many(rows) == 3
    assert [row["id"] for row in empty_table.rows.get_all()] == [0, 1, 2]


def test_insert_many_with_no_rows_returns_zero(people_table):
    before = people_table.rows.get_all()

    assert people_table.rows.insert_many([]) == 0
    assert people_table.rows.get_all() == before


def test_insert_many_counts_only_the_rows_it_adds(people_table):
    count = people_table.rows.insert_many(
        [{"id": 4, "name": "Barbara", "age": 40, "active": True}]
    )

    assert count == 1
    assert len(people_table.rows) == 4


def test_insert_many_applies_defaults_to_each_row():
    default = ["new"]
    table = Table(
        "items",
        {"tags": list[str]},
        defaults={"tags": default},
    )

    table.rows.insert_many([{}, {}])

    first = table.rows.get_one(0)
    first["tags"].append("changed")

    assert table.rows.get_one(1)["tags"] == ["new"]
    assert default == ["new"]


def test_insert_many_prefers_explicit_values_over_defaults():
    table = Table(
        "items",
        {"id": int, "name": str},
        defaults={"name": "unknown"},
    )

    table.rows.insert_many(
        [
            {"id": 1},
            {"id": 2, "name": "Ada"},
        ]
    )

    assert table.rows.get_all() == [
        {"id": 1, "name": "unknown"},
        {"id": 2, "name": "Ada"},
    ]


@pytest.mark.parametrize(
    "invalid",
    [
        {"id": 2},
        {"id": 2, "name": "Linus", "extra": True},
        {"id": "2", "name": "Linus"},
        None,
    ],
)
def test_insert_many_leaves_the_table_unchanged_when_a_row_fails(
    empty_table,
    invalid,
):
    empty_table.rows.insert({"id": 0, "name": "existing"})
    before = empty_table.rows.get_all()

    with pytest.raises((TypeError, ValueError)):
        empty_table.rows.insert_many(
            [
                {"id": 1, "name": "Ada"},
                invalid,
                {"id": 3, "name": "Grace"},
            ]
        )

    assert empty_table.rows.get_all() == before


def test_insert_many_leaves_the_table_unchanged_when_the_iterable_fails(
    empty_table,
):
    def rows():
        yield {"id": 1, "name": "Ada"}
        raise RuntimeError("source failed")

    with pytest.raises(RuntimeError, match="source failed"):
        empty_table.rows.insert_many(rows())

    assert empty_table.rows.get_all() == []
