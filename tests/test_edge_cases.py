"""Edge cases and regression-oriented tests."""

import pytest

from ramtable import Table


def test_empty_strings_are_valid_cell_values():
    table = Table("notes", {"text": str})
    table.rows.insert({"text": ""})

    assert table.rows.get_one(0) == {"text": ""}
    assert table.rows.filter({"text": ""}) == [{"text": ""}]


def test_empty_collections_are_valid_parameterized_values():
    table = Table(
        "collections",
        {
            "numbers": list[int],
            "mapping": dict[str, int],
            "items": set[str],
        },
    )
    table.rows.insert({"numbers": [], "mapping": {}, "items": set()})

    assert table.rows.get_one(0) == {
        "numbers": [],
        "mapping": {},
        "items": set(),
    }


def test_zero_negative_and_large_integers_round_trip():
    table = Table("numbers", {"value": int})
    values = [0, -1, -(10**30), 10**30]

    for value in values:
        table.rows.insert({"value": value})

    assert table.rows.get_column("value") == values
    assert table.rows.filter({"value": {"<": 0}}) == [
        {"value": -1},
        {"value": -(10**30)},
    ]


def test_single_row_table_supports_every_read_and_mutation():
    table = Table("one", {"id": int})
    table.rows.insert({"id": 1})

    assert table.rows.get_one(0) == {"id": 1}
    assert table.rows.get() == [{"id": 1}]
    assert table.rows.filter({"id": 1}) == [{"id": 1}]
    assert table.rows.update({"id": 1}, {"id": 2}) == 1
    assert table.rows.remove({"id": 2}) is None
    assert len(table) == 0

    table.rows.insert({"id": 3})
    assert table.rows.delete({"id": 3}) == 1
    assert len(table) == 0


def test_single_column_table_rejects_removing_its_only_column():
    table = Table("one", {"id": int})

    with pytest.raises(ValueError, match="at least one column"):
        table.columns.remove("id")


def test_column_names_can_contain_spaces_but_not_be_blank():
    table = Table("items", {" item id ": int})
    table.rows.insert({" item id ": 1})

    assert table.rows.get_one(0) == {" item id ": 1}

    with pytest.raises(ValueError):
        table.columns.add("   ", int)


def test_duplicate_values_are_allowed():
    table = Table("items", {"id": int})
    table.rows.insert({"id": 1})
    table.rows.insert({"id": 1})
    table.rows.insert({"id": 1})

    assert table.rows.get_column("id") == [1, 1, 1]
    assert len(table.rows.filter({"id": 1})) == 3
    assert table.rows.delete({"id": 1}) == 3


def test_empty_table_reads_and_columns_are_safe(empty_table):
    assert empty_table.rows.get() == []
    assert empty_table.rows.get_all() == []
    assert empty_table.rows.filter({"id": 1}) == []
    assert empty_table.rows.get_columns() == {"id": [], "name": []}
    assert empty_table.rows.get_columns("name", "id") == {"name": [], "id": []}
    assert empty_table.rows.get_column("id") == []
    assert list(empty_table.rows) == []
    assert len(empty_table.rows) == 0


def test_repeated_insert_clear_cycles_keep_schema():
    table = Table("items", {"id": int})

    for _ in range(3):
        table.rows.insert({"id": 1})
        table.rows.insert({"id": 2})
        assert len(table.rows) == 2
        table.rows.clear()
        assert len(table.rows) == 0
        assert table.columns.get_all() == {"id": int}


def test_repeated_updates_and_deletes_are_deterministic(people_table):
    for _ in range(3):
        people_table.rows.update({"id": 1}, {"active": False})
        people_table.rows.update({"id": 1}, {"active": True})

    assert people_table.rows.get_column("active") == [True, False, True]

    for _ in range(3):
        people_table.rows.delete({"id": {">": 0}})
        assert len(people_table.rows) == 0
        people_table.rows.insert(
            {"id": 1, "name": "Ada", "age": 36, "active": True}
        )


def test_none_is_only_valid_for_optional_or_none_columns():
    table = Table("optional", {"value": int | None})
    table.rows.insert({"value": None})
    table.rows.insert({"value": 1})

    assert table.rows.get_column("value") == [None, 1]

    with pytest.raises(TypeError):
        table.rows.insert({"value": "not an int"})


@pytest.mark.parametrize("index", [True, False])
def test_boolean_indexes_are_rejected_even_though_bool_is_an_int(
    people_table,
    index,
):
    with pytest.raises(TypeError):
        people_table.rows.get(index)

    with pytest.raises(TypeError):
        people_table.rows.get_one(index)


def test_missing_keys_and_unexpected_keys_are_reported_together(empty_table):
    with pytest.raises(ValueError) as error:
        empty_table.rows.insert({"id": 1, "unexpected": True})

    message = str(error.value)
    assert "Missing columns" in message
    assert "Unexpected columns" in message


def test_unexpected_input_types_do_not_mutate_the_table(people_table):
    before = people_table.rows.get_all()

    with pytest.raises(TypeError):
        people_table.rows.insert(["id", "name"])

    with pytest.raises(TypeError):
        people_table.rows.update({"id": 1}, {"age": object()})

    with pytest.raises(ValueError):
        people_table.rows.delete([])

    assert people_table.rows.get_all() == before
