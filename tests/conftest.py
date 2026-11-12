"""Shared fixtures for the RAMTable test suite."""

import pytest

from ramtable import Table


@pytest.fixture
def empty_table():
    """Return a small table with no rows."""
    return Table(
        "empty",
        {
            "id": int,
            "name": str,
        },
    )


@pytest.fixture
def people_table():
    """Return a populated table used by row and mutation tests."""
    table = Table(
        "people",
        {
            "id": int,
            "name": str,
            "age": int,
            "active": bool,
        },
    )

    rows = [
        {"id": 1, "name": "Ada", "age": 36, "active": True},
        {"id": 2, "name": "Linus", "age": 28, "active": False},
        {"id": 3, "name": "Grace", "age": 45, "active": True},
    ]

    for row in rows:
        table.rows.insert(row)

    return table


@pytest.fixture
def inventory_table():
    """Return a table with varied values for filter tests."""
    table = Table(
        "inventory",
        {
            "code": str,
            "description": str,
            "quantity": int,
            "active": bool,
            "tags": list[str],
        },
    )

    rows = [
        {
            "code": "A-10",
            "description": "notebook",
            "quantity": 12,
            "active": True,
            "tags": ["paper", "school"],
        },
        {
            "code": "B-2",
            "description": "pen",
            "quantity": 3,
            "active": True,
            "tags": ["writing"],
        },
        {
            "code": "C-3",
            "description": "archive box",
            "quantity": 0,
            "active": False,
            "tags": ["storage"],
        },
        {
            "code": "D-4",
            "description": "notebook cover",
            "quantity": 5,
            "active": True,
            "tags": ["paper", "cover"],
        },
    ]

    for row in rows:
        table.rows.insert(row)

    return table
