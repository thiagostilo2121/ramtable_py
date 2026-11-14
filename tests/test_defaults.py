"""Tests for insert defaults declared when creating a table."""

import pytest

import ramtable.columns as columns_module
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


def test_add_default_applies_to_future_inserts_on_empty_table():
    table = Table("items", {"id": int})

    table.columns.add("status", str, default="pending")
    table.rows.insert({"id": 1})

    assert table.rows.get_one(0) == {"id": 1, "status": "pending"}


def test_add_fill_value_and_default_stay_independent():
    table = Table("items", {"id": int})
    table.rows.insert({"id": 1})

    table.columns.add(
        "status",
        str,
        fill_value="legacy",
        default="pending",
    )

    assert table.rows.get_one(0) == {"id": 1, "status": "legacy"}

    table.rows.insert({"id": 2})

    assert table.rows.get_one(1) == {"id": 2, "status": "pending"}


def test_add_on_empty_table_uses_the_default_not_the_fill_value():
    table = Table("items", {"id": int})

    table.columns.add(
        "status",
        str,
        fill_value="legacy",
        default="pending",
    )
    table.rows.insert({"id": 1})

    assert table.rows.get_one(0) == {"id": 1, "status": "pending"}


def test_add_default_is_keyword_only():
    table = Table("items", {"id": int})

    with pytest.raises(TypeError, match="positional"):
        table.columns.add("status", str, "legacy", "pending")

    assert "status" not in table.columns


def test_add_default_does_not_replace_a_required_fill_value():
    table = Table("items", {"id": int})
    table.rows.insert({"id": 1})
    rows_before = table.rows.get_all()

    with pytest.raises(ValueError, match="fill value is required"):
        table.columns.add("status", str, default="pending")

    assert "status" not in table.columns
    assert table.rows.get_all() == rows_before


def test_add_rejects_default_that_does_not_match_the_column_type():
    table = Table("items", {"id": int})

    with pytest.raises(
        TypeError,
        match="Default value for column 'status'",
    ):
        table.columns.add("status", int, default="pending")

    assert "status" not in table.columns


def test_add_default_is_deep_copied_for_each_inserted_row():
    default = ["new"]
    table = Table("items", {"id": int})
    table.columns.add("tags", list[str], default=default)

    table.rows.insert({"id": 1})
    table.rows.insert({"id": 2})
    table.rows.get_one(0)["tags"].append("changed")

    assert table.rows.get_one(1)["tags"] == ["new"]
    assert table.columns.get_default("tags") == ["new"]
    assert default == ["new"]


def test_add_accepts_a_none_default_for_an_optional_type():
    table = Table("items", {"id": int})

    table.columns.add("note", str | None, default=None)
    table.rows.insert({"id": 1})

    assert table.rows.get_one(0) == {"id": 1, "note": None}


def test_add_without_a_default_does_not_create_one():
    table = Table("items", {"id": int})

    table.columns.add("status", str)

    with pytest.raises(ValueError, match="does not have a default"):
        table.columns.get_default("status")


def test_add_non_copyable_default_leaves_the_table_unchanged():
    table = Table("items", {"id": int})

    with pytest.raises(
        TypeError,
        match="Default value for column 'value' cannot be deep-copied",
    ):
        table.columns.add("value", object, default=_NotCopyable())

    assert "value" not in table.columns
    assert table.rows.get_all() == []


def test_add_non_copyable_default_with_rows_is_atomic():
    table = Table("items", {"id": int})
    table.rows.insert({"id": 1})
    rows_before = table.rows.get_all()

    with pytest.raises(
        TypeError,
        match="Default value for column 'value' cannot be deep-copied",
    ):
        table.columns.add(
            "value",
            object,
            fill_value="legacy",
            default=_NotCopyable(),
        )

    assert "value" not in table.columns
    assert table.rows.get_all() == rows_before


def test_add_invalid_default_with_rows_is_atomic():
    table = Table("items", {"id": int})
    table.rows.insert({"id": 1})
    rows_before = table.rows.get_all()

    with pytest.raises(
        TypeError,
        match="Default value for column 'status'",
    ):
        table.columns.add(
            "status",
            int,
            fill_value=0,
            default="pending",
        )

    assert "status" not in table.columns
    assert table.rows.get_all() == rows_before


def test_add_non_copyable_fill_value_leaves_the_table_unchanged():
    table = Table("items", {"id": int})
    table.rows.insert({"id": 1})
    rows_before = table.rows.get_all()

    with pytest.raises(
        TypeError,
        match="Fill value cannot be deep-copied",
    ):
        table.columns.add(
            "value",
            object,
            fill_value=_NotCopyable(),
        )

    assert "value" not in table.columns
    assert table.rows.get_all() == rows_before


def test_set_default_applies_to_future_inserts():
    table = Table("items", {"id": int, "status": str})
    table.rows.insert({"id": 1, "status": "done"})

    table.columns.set_default("status", "pending")
    table.rows.insert({"id": 2})

    assert table.rows.get_one(0) == {"id": 1, "status": "done"}
    assert table.rows.get_one(1) == {"id": 2, "status": "pending"}


def test_set_default_replaces_an_existing_default():
    table = Table(
        "items",
        {"status": str},
        defaults={"status": "old"},
    )

    table.columns.set_default("status", "new")

    assert table.columns.get_default("status") == "new"

    table.rows.insert({})

    assert table.rows.get_one(0) == {"status": "new"}


def test_set_default_deep_copies_a_mutable_value():
    default = ["new"]
    table = Table("items", {"tags": list[str]})

    table.columns.set_default("tags", default)
    default.append("changed")

    returned = table.columns.get_default("tags")
    returned.append("changed again")

    table.rows.insert({})

    assert table.rows.get_one(0) == {"tags": ["new"]}
    assert table.columns.get_default("tags") == ["new"]


def test_set_default_accepts_none_for_an_optional_type():
    table = Table("items", {"note": str | None})

    table.columns.set_default("note", None)
    table.rows.insert({})

    assert table.rows.get_one(0) == {"note": None}


def test_set_default_rejects_an_unknown_column():
    table = Table("items", {"id": int})

    with pytest.raises(ValueError, match="does not exist"):
        table.columns.set_default("missing", 1)


def test_set_default_rejects_a_value_incompatible_with_the_type():
    table = Table("items", {"id": int})

    with pytest.raises(
        TypeError,
        match="Default value for column 'id'",
    ):
        table.columns.set_default("id", "1")

    with pytest.raises(ValueError, match="does not have a default"):
        table.columns.get_default("id")


def test_set_default_is_atomic_when_copying_fails():
    table = Table(
        "items",
        {"value": object},
        defaults={"value": "old"},
    )

    with pytest.raises(
        TypeError,
        match="Default value for column 'value' cannot be deep-copied",
    ):
        table.columns.set_default("value", _NotCopyable())

    assert table.columns.get_default("value") == "old"


def test_remove_default_removes_it_from_future_inserts():
    table = Table(
        "items",
        {"id": int, "status": str},
        defaults={"status": "pending"},
    )

    table.columns.remove_default("status")

    with pytest.raises(ValueError, match="does not have a default"):
        table.columns.get_default("status")

    with pytest.raises(ValueError, match="Missing columns"):
        table.rows.insert({"id": 1})

    assert table.columns.get("status") is str


def test_remove_default_rejects_an_unknown_column():
    table = Table("items", {"id": int})

    with pytest.raises(ValueError, match="does not exist"):
        table.columns.remove_default("missing")


def test_remove_default_rejects_a_column_without_a_default():
    table = Table("items", {"id": int})

    with pytest.raises(ValueError, match="does not have a default"):
        table.columns.remove_default("id")


def test_get_defaults_returns_every_default():
    table = Table(
        "items",
        {"id": int, "name": str, "active": bool},
        defaults={"name": "unknown", "active": True},
    )

    assert table.columns.get_defaults() == {
        "name": "unknown",
        "active": True,
    }


def test_get_defaults_returns_an_empty_dictionary_without_defaults():
    table = Table("items", {"id": int})

    assert table.columns.get_defaults() == {}


def test_get_defaults_deep_copies_nested_values():
    default = [{"values": [1]}]
    table = Table(
        "items",
        {"items": list[dict[str, list[int]]]},
        defaults={"items": default},
    )

    defaults = table.columns.get_defaults()
    defaults["items"][0]["values"].append(2)

    assert table.columns.get_defaults() == {
        "items": [{"values": [1]}]
    }
    assert default == [{"values": [1]}]


def test_get_defaults_returns_a_new_dictionary():
    table = Table("items", {"name": str}, defaults={"name": "unknown"})

    defaults = table.columns.get_defaults()
    defaults["extra"] = "value"

    assert "extra" not in table.columns.get_defaults()


def test_set_default_does_not_replace_values_in_existing_rows():
    table = Table("items", {"id": int, "status": str})
    table.rows.insert({"id": 1, "status": "done"})

    table.columns.set_default("status", "pending")

    assert table.rows.get_one(0) == {"id": 1, "status": "done"}


def test_remove_column_drops_a_default_set_after_creation():
    table = Table("items", {"id": int, "status": str})
    table.columns.set_default("status", "pending")

    table.columns.remove("status")

    with pytest.raises(ValueError, match="does not exist"):
        table.columns.get_default("status")

    table.columns.add("status", str)

    with pytest.raises(ValueError, match="does not have a default"):
        table.columns.get_default("status")


def test_update_revalidates_a_default_set_after_creation():
    table = Table("items", {"id": int})
    table.columns.set_default("id", 0)

    with pytest.raises(
        TypeError,
        match="Default value for column 'id'",
    ):
        table.columns.update("id", str)

    assert table.columns.get("id") is int
    assert table.columns.get_default("id") == 0


def test_update_keeps_a_compatible_default():
    table = Table("items", {"id": int})
    table.columns.set_default("id", 0)

    table.columns.update("id", int | str)

    assert table.columns.get_default("id") == 0
    table.rows.insert({})
    assert table.rows.get_one(0) == {"id": 0}


def test_clear_preserves_a_default_set_after_creation():
    table = Table("items", {"status": str})
    table.columns.set_default("status", "pending")
    table.rows.insert({})

    table.clear()
    table.rows.insert({})

    assert table.rows.get_one(0) == {"status": "pending"}
    assert table.columns.get_default("status") == "pending"


def test_insert_does_not_copy_defaults_for_provided_columns(
    monkeypatch,
):
    table = Table(
        "items",
        {"tags": list[str]},
        defaults={"tags": ["default"]},
    )
    copied = []
    real_deepcopy = columns_module.deepcopy

    def tracking_deepcopy(value):
        copied.append(value)
        return real_deepcopy(value)

    monkeypatch.setattr(
        columns_module,
        "deepcopy",
        tracking_deepcopy,
    )

    table.rows.insert({"tags": ["explicit"]})

    assert copied == []


def test_insert_copies_defaults_only_for_omitted_columns(monkeypatch):
    table = Table(
        "items",
        {"id": int, "tags": list[str]},
        defaults={"tags": ["default"]},
    )
    copied = []
    real_deepcopy = columns_module.deepcopy

    def tracking_deepcopy(value):
        copied.append(value)
        return real_deepcopy(value)

    monkeypatch.setattr(
        columns_module,
        "deepcopy",
        tracking_deepcopy,
    )

    table.rows.insert({"id": 1})

    assert copied == [["default"]]
    assert table.rows.get_one(0) == {"id": 1, "tags": ["default"]}


def test_get_default_reports_a_copy_failure(monkeypatch):
    table = Table(
        "items",
        {"value": object},
        defaults={"value": "old"},
    )

    def failing_deepcopy(value):
        raise TypeError("cannot copy")

    monkeypatch.setattr(
        columns_module,
        "deepcopy",
        failing_deepcopy,
    )

    with pytest.raises(
        TypeError,
        match="Default value for column 'value' cannot be deep-copied",
    ):
        table.columns.get_default("value")


def test_get_defaults_reports_a_copy_failure(monkeypatch):
    table = Table(
        "items",
        {"value": object},
        defaults={"value": "old"},
    )

    def failing_deepcopy(value):
        raise TypeError("cannot copy")

    monkeypatch.setattr(
        columns_module,
        "deepcopy",
        failing_deepcopy,
    )

    with pytest.raises(
        TypeError,
        match="Default value for column 'value' cannot be deep-copied",
    ):
        table.columns.get_defaults()
