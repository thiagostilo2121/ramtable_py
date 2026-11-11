"""Integration tests across Table, Rows, and Columns."""

from ramtable import Table


def assert_rows_match_schema(table):
    """Assert that every stored row has exactly the table's columns."""
    schema = set(table.columns.get_all())

    for row in table.rows.get_all():
        assert set(row) == schema


def test_full_table_workflow_keeps_rows_and_schema_consistent():
    table = Table(
        "people",
        {
            "id": int,
            "name": str,
            "age": int,
        },
    )

    table.rows.insert({"id": 1, "name": "Ada", "age": 36})
    table.rows.insert({"id": 2, "name": "Linus", "age": 28})
    table.rows.insert({"id": 3, "name": "Grace", "age": 45})

    assert table.rows.filter({"age": {">=": 36}}) == [
        {"id": 1, "name": "Ada", "age": 36},
        {"id": 3, "name": "Grace", "age": 45},
    ]

    updated = table.rows.update(
        {"age": {"<": 30}},
        {"name": "Linus Torvalds"},
    )
    assert updated == 1
    assert table.rows.get_one(1)["name"] == "Linus Torvalds"

    assert table.rows.delete({"id": 1}) == 1
    assert table.rows.get_column("id") == [2, 3]

    table.columns.add("active", bool, default=True)
    assert table.rows.get_column("active") == [True, True]

    table.columns.remove("age")
    assert table.columns.get_all() == {"id": int, "name": str, "active": bool}
    assert_rows_match_schema(table)

    table.rows.insert({"id": 3, "name": "Grace Hopper", "active": True})
    assert table.rows.get_column("id") == [2, 3, 3]
    assert_rows_match_schema(table)


def test_row_copies_share_mutable_values_but_not_dictionaries():
    table = Table("items", {"id": int, "tags": list[str]})
    source = {"id": 1, "tags": ["original"]}

    table.rows.insert(source)
    source["tags"].append("from source")

    fetched = table.rows.get_one(0)
    fetched["id"] = 99
    fetched["tags"].append("from fetch")

    filtered = table.rows.filter({"id": 1})[0]
    filtered["tags"].append("from filter")

    stored = table.rows.get_one(0)
    assert stored["id"] == 1
    assert stored["tags"] == [
        "original",
        "from source",
        "from fetch",
        "from filter",
    ]


def test_get_columns_reflects_updates_and_deletions():
    table = Table("items", {"id": int, "name": str})
    table.rows.insert({"id": 1, "name": "one"})
    table.rows.insert({"id": 2, "name": "two"})
    table.rows.insert({"id": 3, "name": "three"})

    table.rows.update({"id": 2}, {"name": "TWO"})
    table.rows.delete({"id": 1})

    assert table.rows.get_columns("id", "name") == {
        "id": [2, 3],
        "name": ["TWO", "three"],
    }
    assert len(table) == 2


def test_multiple_consecutive_mutations_preserve_invariants():
    table = Table("items", {"id": int, "name": str})

    for index in range(1, 6):
        table.rows.insert({"id": index, "name": f"item-{index}"})
        assert_rows_match_schema(table)

    table.rows.update({"id": {">=": 3}}, {"name": "updated"})
    table.columns.add("active", bool, default=True)
    table.rows.delete({"id": {">": 4}})
    table.columns.remove("name")
    table.rows.insert({"id": 10, "active": False})

    assert table.rows.get_all() == [
        {"id": 1, "active": True},
        {"id": 2, "active": True},
        {"id": 3, "active": True},
        {"id": 4, "active": True},
        {"id": 10, "active": False},
    ]
    assert_rows_match_schema(table)


def test_large_table_filter_update_and_delete():
    table = Table("numbers", {"value": int, "label": str})

    for value in range(1000):
        label = "even" if value % 2 == 0 else "odd"
        table.rows.insert({"value": value, "label": label})

    assert len(table.rows.filter({"label": "even"})) == 500
    assert len(table.rows.filter({"value": {">=": 500}})) == 500

    updated = table.rows.update({"value": {">=": 900}}, {"label": "high"})
    assert updated == 100
    assert len(table.rows.filter({"label": "high"})) == 100

    deleted = table.rows.delete({"label": "odd"})
    assert deleted == 450
    assert len(table) == 550
    assert_rows_match_schema(table)


def test_nested_data_and_none_values_round_trip():
    table = Table(
        "events",
        {
            "id": int,
            "payload": dict[str, list[int]],
            "note": str | None,
        },
    )
    table.rows.insert(
        {
            "id": 1,
            "payload": {"values": [1, 2, 3]},
            "note": None,
        }
    )
    table.rows.insert(
        {
            "id": 2,
            "payload": {"values": []},
            "note": "ready",
        }
    )

    assert table.rows.get_one(0)["payload"] == {"values": [1, 2, 3]}
    assert table.rows.get_one(0)["note"] is None
    assert table.rows.filter({"note": None}) == [
        {"id": 1, "payload": {"values": [1, 2, 3]}, "note": None},
    ]
