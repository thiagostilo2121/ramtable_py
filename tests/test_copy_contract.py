"""Contract tests for RAMTable's copying behavior.

Inserts and reads return shallow dictionary copies, so nested values keep
their identity. Fill values and insert defaults are deep-copied once per
row.
"""

from ramtable import Table


def test_insert_stores_a_shallow_copy_of_the_row():
    table = Table("items", {"id": int, "tags": list[str]})
    row = {"id": 1, "tags": ["new"]}

    table.rows.insert(row)

    assert table.rows.get_one(0) is not row
    assert table.rows.get_one(0)["tags"] is row["tags"]

    row["id"] = 2

    assert table.rows.get_one(0)["id"] == 1


def test_changing_a_returned_row_does_not_change_the_stored_row():
    table = Table("items", {"id": int, "tags": list[str]})
    table.rows.insert({"id": 1, "tags": ["new"]})

    returned = table.rows.get_one(0)
    returned["id"] = 2

    assert table.rows.get_one(0)["id"] == 1


def test_mutating_a_nested_value_is_visible_through_every_copy():
    table = Table("items", {"id": int, "tags": list[str]})
    table.rows.insert({"id": 1, "tags": ["new"]})

    table.rows.get_one(0)["tags"].append("changed")

    assert table.rows.get_one(0)["tags"] == ["new", "changed"]
    assert table.rows.get_all()[0]["tags"] == ["new", "changed"]


def test_reads_return_new_dictionaries_that_share_nested_values():
    table = Table("items", {"id": int, "tags": list[str]})
    table.rows.insert({"id": 1, "tags": ["new"]})

    single = table.rows.get_one(0)
    many = table.rows.get(0)
    every = table.rows.get_all()
    filtered = table.rows.filter({"id": 1})
    iterated = list(table.rows)

    copies = [single, many[0], every[0], filtered[0], iterated[0]]

    for copy in copies:
        assert copy == {"id": 1, "tags": ["new"]}
        assert copy["tags"] is single["tags"]

    assert len({id(copy) for copy in copies}) == len(copies)


def test_fill_value_is_deep_copied_for_each_existing_row():
    table = Table("items", {"id": int})
    table.rows.insert({"id": 1})
    table.rows.insert({"id": 2})
    fill = {"labels": ["new"]}

    table.columns.add("meta", dict[str, list[str]], fill_value=fill)

    first = table.rows.get_one(0)
    second = table.rows.get_one(1)

    assert first["meta"] == {"labels": ["new"]}
    assert first["meta"] is not fill
    assert first["meta"] is not second["meta"]
    assert first["meta"]["labels"] is not fill["labels"]

    first["meta"]["labels"].append("changed")

    assert table.rows.get_one(0)["meta"] == {
        "labels": ["new", "changed"]
    }
    assert table.rows.get_one(1)["meta"] == {"labels": ["new"]}
    assert fill == {"labels": ["new"]}


def test_insert_default_is_deep_copied_for_each_row():
    default = {"labels": ["new"]}
    table = Table(
        "items",
        {"id": int, "meta": dict[str, list[str]]},
        defaults={"meta": default},
    )

    table.rows.insert({"id": 1})
    table.rows.insert({"id": 2})

    first = table.rows.get_one(0)
    second = table.rows.get_one(1)

    assert first["meta"] is not default
    assert first["meta"] is not second["meta"]

    first["meta"]["labels"].append("changed")

    assert table.rows.get_one(0)["meta"] == {
        "labels": ["new", "changed"]
    }
    assert table.rows.get_one(1)["meta"] == {"labels": ["new"]}
    assert table.columns.get_default("meta") == {"labels": ["new"]}
    assert default == {"labels": ["new"]}


def test_column_add_default_is_deep_copied_for_each_row():
    default = ["new"]
    table = Table("items", {"id": int})

    table.columns.add("tags", list[str], default=default)
    table.rows.insert({"id": 1})
    table.rows.insert({"id": 2})

    first = table.rows.get_one(0)
    second = table.rows.get_one(1)

    assert first["tags"] is not default
    assert first["tags"] is not second["tags"]

    first["tags"].append("changed")

    assert table.rows.get_one(0)["tags"] == ["new", "changed"]
    assert table.rows.get_one(1)["tags"] == ["new"]
    assert table.columns.get_default("tags") == ["new"]
