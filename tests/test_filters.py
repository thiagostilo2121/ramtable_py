"""Tests for the shared filter-condition engine."""

import pytest

from ramtable import Table


def codes(rows):
    """Return the ``code`` values from a list of inventory rows."""
    return [row["code"] for row in rows]


@pytest.mark.parametrize(
    ("where", "expected"),
    [
        ({"quantity": {"==": 3}}, ["B-2"]),
        ({"quantity": {"!=": 3}}, ["A-10", "C-3", "D-4"]),
        ({"quantity": {">": 5}}, ["A-10"]),
        ({"quantity": {">=": 5}}, ["A-10", "D-4"]),
        ({"quantity": {"<": 5}}, ["B-2", "C-3"]),
        ({"quantity": {"<=": 5}}, ["B-2", "C-3", "D-4"]),
        ({"code": {"in": ["A-10", "C-3"]}}, ["A-10", "C-3"]),
        ({"code": {"not_in": ["A-10", "C-3"]}}, ["B-2", "D-4"]),
        ({"description": {"contains": "note"}}, ["A-10", "D-4"]),
        ({"tags": {"contains": "paper"}}, ["A-10", "D-4"]),
        ({"code": {"startswith": "A"}}, ["A-10"]),
        ({"code": {"endswith": "2"}}, ["B-2"]),
        ({"code": {"startswith": "C", "endswith": "3"}}, ["C-3"]),
    ],
)
def test_filter_supports_every_operator(inventory_table, where, expected):
    assert codes(inventory_table.rows.filter(where)) == expected


def test_filter_uses_equality_for_plain_values(inventory_table):
    assert codes(inventory_table.rows.filter({"active": True})) == [
        "A-10",
        "B-2",
        "D-4",
    ]


def test_filter_combines_multiple_columns_with_and(inventory_table):
    rows = inventory_table.rows.filter({"active": True, "quantity": {">": 5}})

    assert codes(rows) == ["A-10"]


def test_filter_allows_multiple_operators_for_the_same_column(inventory_table):
    rows = inventory_table.rows.filter({"quantity": {">=": 3, "<": 12}})

    assert codes(rows) == ["B-2", "D-4"]


def test_filter_supports_callable_conditions(inventory_table):
    rows = inventory_table.rows.filter({"code": lambda code: len(code) <= 3})

    assert codes(rows) == ["B-2", "C-3", "D-4"]


def test_filter_callable_receives_the_cell_value(inventory_table):
    received = []

    def record(value):
        received.append(value)
        return value > 5

    inventory_table.rows.filter({"quantity": record})

    assert received == [12, 3, 0, 5]
    assert codes(inventory_table.rows.filter({"quantity": record})) == ["A-10"]


def test_filter_callable_uses_truthiness(inventory_table):
    rows = inventory_table.rows.filter({"quantity": lambda quantity: quantity})

    assert codes(rows) == ["A-10", "B-2", "D-4"]


def test_filter_propagates_callable_exceptions(inventory_table):
    def fail(value):
        raise RuntimeError(f"cannot evaluate {value}")

    with pytest.raises(RuntimeError, match="cannot evaluate"):
        inventory_table.rows.filter({"quantity": fail})


def test_filter_returns_an_empty_list_when_nothing_matches(inventory_table):
    assert inventory_table.rows.filter({"code": "missing"}) == []


def test_filter_preserves_storage_order(inventory_table):
    rows = inventory_table.rows.filter({"active": True})

    assert [row["code"] for row in rows] == ["A-10", "B-2", "D-4"]


def test_filter_returns_new_row_dictionaries(inventory_table):
    row = inventory_table.rows.filter({"code": "A-10"})[0]
    row["description"] = "Changed"

    assert inventory_table.rows.get_one(0)["description"] == "notebook"


def test_filter_does_not_validate_condition_values_against_column_types(
    inventory_table,
):
    assert inventory_table.rows.filter({"quantity": {"==": "3"}}) == []

    with pytest.raises(TypeError):
        inventory_table.rows.filter({"quantity": {">": "three"}})


def test_filter_supports_dictionary_values_with_the_equality_operator():
    table = Table("items", {"metadata": dict[str, str]})
    table.rows.insert({"metadata": {"origin": "import"}})
    table.rows.insert({"metadata": {"origin": "manual"}})

    rows = table.rows.filter({"metadata": {"==": {"origin": "import"}}})

    assert rows == [{"metadata": {"origin": "import"}}]


def test_a_dictionary_condition_is_always_an_operator_specification():
    table = Table("items", {"metadata": dict[str, str]})
    table.rows.insert({"metadata": {"origin": "import"}})

    with pytest.raises(ValueError, match="Unknown filter operator"):
        table.rows.filter({"metadata": {"origin": "import"}})


@pytest.mark.parametrize("where", [None, [], "", 0, {}])
def test_filter_rejects_invalid_condition_containers(inventory_table, where):
    with pytest.raises(ValueError, match="non-empty dictionary"):
        inventory_table.rows.filter(where)


def test_filter_rejects_missing_columns(inventory_table):
    with pytest.raises(ValueError, match="does not exist"):
        inventory_table.rows.filter({"missing": 1})


@pytest.mark.parametrize("condition", [{}, {"<>": 1}, {"==": 1, "bad": 2}])
def test_filter_rejects_invalid_column_conditions(inventory_table, condition):
    with pytest.raises(ValueError):
        inventory_table.rows.filter({"quantity": condition})
