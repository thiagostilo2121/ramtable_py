"""Tests for insert defaults declared when creating a table."""

import pytest

from ramtable import Table


def test_insert_fills_missing_columns_from_defaults():
    table = Table(
        "items",
        {"id": int, "name": str, "active": bool},
        defaults={"name": "unknown", "active": True},
    )

    table.rows.insert({"id": 1})

    assert table.rows.get_one(0) == {
        "id": 1,
        "name": "unknown",
        "active": True,
    }


def test_insert_prefers_explicit_values_over_defaults():
    table = Table(
        "items",
        {"id": int, "name": str},
        defaults={"name": "unknown"},
    )

    table.rows.insert({"id": 1, "name": "Ada"})

    assert table.rows.get_one(0) == {"id": 1, "name": "Ada"}


def test_insert_still_requires_columns_without_defaults():
    table = Table(
        "items",
        {"id": int, "name": str},
        defaults={"id": 0},
    )

    with pytest.raises(ValueError, match="Missing columns") as error:
        table.rows.insert({})

    assert "'name'" in str(error.value)


def test_insert_rejects_unknown_columns_even_with_defaults():
    table = Table("items", {"id": int}, defaults={"id": 0})

    with pytest.raises(ValueError, match="Unexpected columns"):
        table.rows.insert({"id": 1, "extra": 2})


def test_insert_does_not_modify_the_caller_row():
    table = Table(
        "items",
        {"id": int, "name": str},
        defaults={"name": "unknown"},
    )
    row = {"id": 1}

    table.rows.insert(row)

    assert row == {"id": 1}


def test_empty_defaults_keep_every_column_required():
    table = Table("items", {"id": int}, defaults={})

    with pytest.raises(ValueError, match="Missing columns"):
        table.rows.insert({})


def test_defaults_must_be_a_dictionary():
    with pytest.raises(TypeError, match="must be a dictionary"):
        Table("items", {"id": int}, defaults=[])


def test_default_for_unknown_column_is_rejected():
    with pytest.raises(ValueError, match="unknown column 'missing'"):
        Table(
            "items",
            {"id": int},
            defaults={"missing": 1},
        )


def test_default_must_match_the_column_type():
    with pytest.raises(TypeError, match="Default value for column 'id'"):
        Table(
            "items",
            {"id": int},
            defaults={"id": "1"},
        )


class _NotCopyable:
    def __deepcopy__(self, memo):
        raise TypeError("cannot copy")


def test_non_copyable_default_raises_a_clear_type_error():
    value = _NotCopyable()

    with pytest.raises(
        TypeError,
        match="Default value for column 'value' cannot be deep-copied",
    ) as error:
        Table(
            "items",
            {"value": _NotCopyable},
            defaults={"value": value},
        )

    assert isinstance(error.value.__cause__, TypeError)


def test_none_is_a_valid_default_for_optional_types():
    table = Table(
        "items",
        {"note": str | None},
        defaults={"note": None},
    )

    table.rows.insert({})

    assert table.rows.get_one(0) == {"note": None}


def test_none_default_must_match_the_column_type():
    with pytest.raises(TypeError, match="Default value for column 'id'"):
        Table(
            "items",
            {"id": int},
            defaults={"id": None},
        )


def test_explicit_none_is_not_replaced_by_a_default():
    table = Table(
        "items",
        {"note": str | None},
        defaults={"note": "missing"},
    )

    table.rows.insert({"note": None})

    assert table.rows.get_one(0) == {"note": None}


def test_get_default_returns_a_deep_copy():
    default = ["new"]
    table = Table(
        "items",
        {"tags": list[str]},
        defaults={"tags": default},
    )

    value = table.columns.get_default("tags")
    value.append("changed")

    assert table.columns.get_default("tags") == ["new"]
    assert default == ["new"]


def test_get_default_requires_an_existing_column():
    table = Table("items", {"id": int})

    with pytest.raises(ValueError, match="does not exist"):
        table.columns.get_default("missing")


def test_get_default_reports_columns_without_a_default():
    table = Table(
        "items",
        {"id": int, "name": str},
        defaults={"id": 0},
    )

    with pytest.raises(ValueError, match="does not have a default"):
        table.columns.get_default("name")


def test_mutable_defaults_are_copied_for_each_inserted_row():
    default = ["new"]
    table = Table(
        "items",
        {"tags": list[str]},
        defaults={"tags": default},
    )

    table.rows.insert({})
    table.rows.insert({})

    first = table.rows.get_one(0)
    first["tags"].append("changed")

    assert table.rows.get_one(0)["tags"] == ["new", "changed"]
    assert table.rows.get_one(1)["tags"] == ["new"]
    assert default == ["new"]


def test_nested_list_defaults_are_isolated_between_rows():
    default = [{"values": [1]}]
    table = Table(
        "items",
        {"items": list[dict[str, list[int]]]},
        defaults={"items": default},
    )

    table.rows.insert({})
    table.rows.insert({})

    first = table.rows.get_one(0)
    first["items"][0]["values"].append(2)

    assert table.rows.get_one(0)["items"] == [{"values": [1, 2]}]
    assert table.rows.get_one(1)["items"] == [{"values": [1]}]
    assert default == [{"values": [1]}]


def test_nested_dictionary_defaults_are_isolated_between_rows():
    default = {"tags": ["new"]}
    table = Table(
        "items",
        {"meta": dict[str, list[str]]},
        defaults={"meta": default},
    )

    table.rows.insert({})
    table.rows.insert({})

    first = table.rows.get_one(0)
    first["meta"]["tags"].append("changed")

    assert table.rows.get_one(0)["meta"] == {"tags": ["new", "changed"]}
    assert table.rows.get_one(1)["meta"] == {"tags": ["new"]}
    assert default == {"tags": ["new"]}


def test_get_default_deep_copies_nested_values():
    default = [{"values": [1]}]
    table = Table(
        "items",
        {"items": list[dict[str, list[int]]]},
        defaults={"items": default},
    )

    value = table.columns.get_default("items")
    value[0]["values"].append(2)

    assert table.columns.get_default("items") == [{"values": [1]}]
    assert default == [{"values": [1]}]


def test_mutating_the_original_default_does_not_affect_the_table():
    default = ["new"]
    table = Table(
        "items",
        {"tags": list[str]},
        defaults={"tags": default},
    )

    default.append("changed")
    table.rows.insert({})

    assert table.rows.get_one(0) == {"tags": ["new"]}


def test_clear_preserves_insert_defaults():
    table = Table("items", {"name": str}, defaults={"name": "unknown"})
    table.rows.insert({})
    table.clear()

    table.rows.insert({})

    assert table.rows.get_one(0) == {"name": "unknown"}


def test_remove_drops_the_column_default():
    table = Table(
        "items",
        {"id": int, "name": str},
        defaults={"name": "unknown"},
    )

    table.columns.remove("name")

    with pytest.raises(ValueError, match="does not exist"):
        table.columns.get_default("name")


def test_recreating_a_removed_column_does_not_restore_its_default():
    table = Table(
        "items",
        {"id": int, "name": str},
        defaults={"name": "unknown"},
    )
    table.rows.insert({"id": 1})
    table.columns.remove("name")

    with pytest.raises(ValueError, match="does not exist"):
        table.columns.get_default("name")

    table.columns.add("name", str, fill_value="new")

    assert table.rows.get_one(0) == {"id": 1, "name": "new"}

    with pytest.raises(ValueError, match="does not have a default"):
        table.columns.get_default("name")

    with pytest.raises(ValueError, match="Missing columns"):
        table.rows.insert({"id": 2})


def test_update_rejects_a_type_incompatible_with_the_default():
    table = Table("items", {"id": int}, defaults={"id": 0})

    with pytest.raises(TypeError, match="Default value for column 'id'"):
        table.columns.update("id", str)

    assert table.columns.get("id") is int


def test_update_accepts_a_type_compatible_with_the_default():
    table = Table("items", {"id": int}, defaults={"id": 0})

    table.columns.update("id", int | str)

    assert table.columns.get("id") == int | str
    table.rows.insert({})
    assert table.rows.get_one(0) == {"id": 0}


def test_columns_add_fill_value_is_not_an_insert_default():
    table = Table("items", {"id": int})
    table.columns.add("score", int, fill_value=10)

    table.rows.insert({"id": 1, "score": 20})

    with pytest.raises(ValueError, match="Missing columns"):
        table.rows.insert({"id": 2})


def test_columns_add_does_not_change_existing_insert_defaults():
    table = Table(
        "items",
        {"id": int, "active": bool},
        defaults={"active": True},
    )
    table.rows.insert({"id": 1})
    table.columns.add("score", int, fill_value=10)

    assert table.columns.get_default("active") is True
    assert table.rows.get_one(0) == {
        "id": 1,
        "active": True,
        "score": 10,
    }

    with pytest.raises(ValueError, match="does not have a default"):
        table.columns.get_default("score")

    table.rows.insert({"id": 2, "score": 20})

    assert table.rows.get_one(1) == {
        "id": 2,
        "active": True,
        "score": 20,
    }

    with pytest.raises(ValueError, match="Missing columns"):
        table.rows.insert({"id": 3})


def test_remove_does_not_apply_insert_defaults():
    table = Table(
        "items",
        {"id": int, "name": str},
        defaults={"name": "unknown"},
    )
    table.rows.insert({"id": 1})

    with pytest.raises(ValueError, match="Missing columns"):
        table.rows.remove({"id": 1})
