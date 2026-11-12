"""Tests for recursive annotation support and runtime type matching."""

from typing import (
    AbstractSet,
    Annotated,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
)

import pytest

from ramtable.types import TypeValidator


@pytest.mark.parametrize(
    "annotation",
    [
        Any,
        None,
        type(None),
        int,
        float,
        str,
        bool,
        bytes,
        object,
        int | str,
        Union[int, str],
        Optional[int],
        Annotated[int, "positive"],
        Annotated[list[int], "values"],
        Literal["pending", "done"],
        Literal[1, 2],
        list,
        list[int],
        list[list[int]],
        List[int],
        set[int],
        frozenset[str],
        Sequence[int],
        Set[int],
        AbstractSet[int],
        dict,
        dict[str, int],
        Dict[str, int],
        Mapping[str, list[int]],
        tuple,
        tuple[int, str],
        tuple[int, ...],
        Tuple[int, ...],
        type[int],
    ],
)
def test_supported_annotation_forms(annotation):
    assert TypeValidator.is_supported_type(annotation) is True


@pytest.mark.parametrize(
    "annotation",
    [
        list[int, str],
        dict[str],
        dict[str, int, float],
        tuple[int, str, ...],
        Callable[[int], int],
        Iterable[int],
        TypeVar("T"),
        Annotated[Callable[[int], int], "callable"],
        Union[int, Callable[[int], int]],
        object(),
    ],
)
def test_unsupported_annotation_forms(annotation):
    assert TypeValidator.is_supported_type(annotation) is False


@pytest.mark.parametrize(
    ("value", "annotation"),
    [
        (1, Any),
        (None, Any),
        ([], Any),
        (None, None),
        (None, type(None)),
        (1, int),
        (True, int),
        (1.5, float),
        ("text", str),
        (True, bool),
        (b"bytes", bytes),
        (object(), object),
        (1, int | str),
        ("text", int | str),
        (None, Optional[int]),
        (1, Optional[int]),
        (10, Annotated[int, "positive"]),
        (-10, Annotated[int, "positive"]),
        ("pending", Literal["pending", "done"]),
        (1, Literal[1, 2]),
    ],
)
def test_matches_type_for_scalars_and_unions(value, annotation):
    assert TypeValidator.matches_type(value, annotation) is True


@pytest.mark.parametrize(
    ("value", "annotation"),
    [
        ("1", int),
        (1, str),
        (1, float),
        (0, bool),
        (None, int),
        (1, None),
        (1, type(None)),
        (True, Literal[1]),
        (1, Literal[True]),
        ("pending", Literal["done"]),
        (1.5, int | str),
        (None, int | str),
    ],
)
def test_matches_type_rejects_incompatible_values(value, annotation):
    assert TypeValidator.matches_type(value, annotation) is False


def test_none_annotation_only_matches_none():
    assert TypeValidator.matches_type(None, None) is True
    assert TypeValidator.matches_type(0, None) is False
    assert TypeValidator.matches_type(False, None) is False


def test_literal_compares_value_and_exact_type():
    assert TypeValidator.matches_type(True, Literal[1]) is False
    assert TypeValidator.matches_type(1, Literal[True]) is False
    assert TypeValidator.matches_type(True, Literal[True]) is True


def test_annotated_ignores_metadata_and_checks_only_the_base_type():
    annotation = Annotated[int, "must be positive"]

    assert TypeValidator.matches_type(-1, annotation) is True
    assert TypeValidator.matches_type("1", annotation) is False


@pytest.mark.parametrize(
    ("value", "annotation"),
    [
        ([], list[int]),
        ([1, 2], list[int]),
        ([True], list[int]),
        ([[1], [2]], list[list[int]]),
        ({1, 2}, set[int]),
        (frozenset({"a"}), frozenset[str]),
        ([1, 2], Sequence[int]),
        ((1, 2), Sequence[int]),
        ("ab", Sequence[str]),
        ({1, 2}, Set[int]),
        (frozenset({1, 2}), AbstractSet[int]),
        ({}, dict[str, int]),
        ({"a": 1}, dict[str, int]),
        ({"a": [1, 2]}, Mapping[str, list[int]]),
        ((), tuple),
        ((1, "a"), tuple[int, str]),
        ((1, 2, 3), tuple[int, ...]),
        (int, type[int]),
        (bool, type[int]),
    ],
)
def test_matches_type_for_collections_and_class_objects(value, annotation):
    assert TypeValidator.matches_type(value, annotation) is True


@pytest.mark.parametrize(
    ("value", "annotation"),
    [
        ([1, "2"], list[int]),
        ((1, 2), list[int]),
        (["1"], list[int]),
        ([[1], ["2"]], list[list[int]]),
        ({1, "2"}, set[int]),
        (frozenset({1, 2}), set[int]),
        (frozenset({1, 2}), Set[int]),
        ({"a": "1"}, dict[str, int]),
        ({1: 1}, dict[str, int]),
        (1, dict[str, int]),
        ({"a": [1, "2"]}, Mapping[str, list[int]]),
        ((1,), tuple[int, str]),
        ((1, "a", 2), tuple[int, str]),
        ((1, "a"), tuple[int, ...]),
        (1, tuple[int, ...]),
        (1, Sequence[int]),
        (1, AbstractSet[int]),
        (1, type[int]),
        (str, type[int]),
    ],
)
def test_matches_type_rejects_invalid_collections_and_class_objects(
    value,
    annotation,
):
    assert TypeValidator.matches_type(value, annotation) is False


def test_parameterized_containers_accept_empty_instances():
    assert TypeValidator.matches_type([], list[int]) is True
    assert TypeValidator.matches_type({}, dict[str, int]) is True
    assert TypeValidator.matches_type(set(), set[int]) is True
    assert TypeValidator.matches_type((), tuple[int, ...]) is True


def test_unparameterized_containers_ignore_element_types():
    assert TypeValidator.matches_type([1, "two", None], list) is True
    assert TypeValidator.matches_type({"a": object()}, dict) is True
    assert TypeValidator.matches_type((1, "two"), tuple) is True


def test_matches_type_rejects_non_container_values_for_container_annotations():
    assert TypeValidator.matches_type(1, list[int]) is False
