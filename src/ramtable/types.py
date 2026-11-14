
"""Recursive validation of type annotations for RAMTable."""

import types as std_types
from collections import abc
from typing import Annotated, Any, Literal, Union, get_args, get_origin


class TypeValidator:
    """Check supported annotations and whether values match them.

    Validation is performed at runtime; it does not convert values or
    implement every static type-checking rule.
    """

    @classmethod
    def is_supported_type(cls, value_type: object) -> bool:
        """Return whether ``value_type`` is an annotation RAMTable can check.

        Supported forms include classes, ``Any``, ``None``, ``Annotated``,
        unions, ``Literal``, common parameterized collections, fixed or
        variadic tuples, and ``type[T]``. Other annotation forms return
        ``False``. This checks the annotation form only; it does not
        validate a value or run validators embedded in ``Annotated``
        metadata.

        Args:
            value_type: Class or annotation to check.

        Returns:
            ``True`` if the annotation form is supported, otherwise
            ``False``.
        """
        if value_type is Any or value_type is None:
            return True

        if isinstance(value_type, type):
            return True

        origin = get_origin(value_type)
        args = get_args(value_type)

        if origin is Annotated:
            return bool(args) and cls.is_supported_type(args[0])

        if origin in (Union, std_types.UnionType):
            return bool(args) and all(
                cls.is_supported_type(arg) for arg in args
            )

        if origin is Literal:
            return bool(args)

        if origin in (list, set, frozenset, abc.Sequence, abc.Set):
            return not args or (
                len(args) == 1
                and cls.is_supported_type(args[0])
            )

        if origin in (dict, abc.Mapping):
            return not args or (
                len(args) == 2
                and all(cls.is_supported_type(arg) for arg in args)
            )

        if origin is tuple:
            if not args:
                return True

            if len(args) == 2 and args[1] is Ellipsis:
                return cls.is_supported_type(args[0])

            return all(cls.is_supported_type(arg) for arg in args)

        if origin is type:
            return (
                len(args) == 1
                and isinstance(args[0], type)
            )

        return False

    @classmethod
    def matches_type(cls, value: object, value_type: object) -> bool:
        """Recursively check whether ``value`` matches ``value_type``.

        Simple types follow Python's ``isinstance`` semantics (for example,
        ``bool`` also matches ``int``). ``Annotated`` checks its base type;
        ``Literal`` requires equality and an exact type match. Elements and
        keys in parameterized containers are also checked. The value is not
        converted.

        Args:
            value: Object to validate.
            value_type: Supported class or annotation.

        Returns:
            ``True`` if the value matches, otherwise ``False``. If a class
            annotation cannot be used with ``isinstance``, this method
            returns ``False``.
        """
        if value_type is Any:
            return True

        if value_type is None:
            return value is None

        origin = get_origin(value_type)
        args = get_args(value_type)

        if origin is Annotated:
            return cls.matches_type(value, args[0])

        if origin in (Union, std_types.UnionType):
            return any(
                cls.matches_type(value, arg) for arg in args
            )

        if origin is Literal:
            return any(
                value == literal and type(value) is type(literal)
                for literal in args
            )

        if origin in (list, set, frozenset):
            if not isinstance(value, origin):
                return False

            return not args or all(
                cls.matches_type(item, args[0])
                for item in value
            )

        if origin is tuple:
            if not isinstance(value, tuple):
                return False

            if not args:
                return True

            if len(args) == 2 and args[1] is Ellipsis:
                return all(
                    cls.matches_type(item, args[0])
                    for item in value
                )

            return (
                len(value) == len(args)
                and all(
                    cls.matches_type(item, expected)
                    for item, expected in zip(value, args)
                )
            )

        if origin in (dict, abc.Mapping):
            if not isinstance(value, origin):
                return False

            if not args:
                return True

            key_type, item_type = args

            return all(
                cls.matches_type(key, key_type)
                and cls.matches_type(item, item_type)
                for key, item in value.items()
            )

        if origin is abc.Sequence:
            if not isinstance(value, abc.Sequence):
                return False

            return not args or all(
                cls.matches_type(item, args[0])
                for item in value
            )

        if origin is abc.Set:
            if not isinstance(value, abc.Set):
                return False

            return not args or all(
                cls.matches_type(item, args[0])
                for item in value
            )

        if origin is type:
            if not isinstance(value, type):
                return False

            try:
                return issubclass(value, args[0])
            except TypeError:
                return False

        try:
            return isinstance(value, value_type)
        except TypeError:
            return False
