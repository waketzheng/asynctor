# Copied from source code of Django 6.0(0174a8)
# And improve type hints without change any code logic
import enum
from enum import IntEnum
from typing import TYPE_CHECKING, Any

try:
    from enum import EnumType, StrEnum
    from enum import property as enum_property
except ImportError as e:
    raise type(e)("This module only support Python3.11+") from e

if TYPE_CHECKING:
    from collections.abc import Iterator, ValuesView

__all__ = ["Choices", "IntegerChoices", "TextChoices"]


class Promise:
    """
    Base class for the proxy class created in the closure of the lazy function.
    It's used to recognize promises in code.
    """

    pass


class ChoicesType(EnumType):
    """A metaclass for creating a enum choices."""

    def __new__(metacls, classname, bases, classdict, **kwds) -> "ChoicesType":
        labels = []
        for key in classdict._member_names:
            value = classdict[key]
            if (
                isinstance(value, (list, tuple))
                and len(value) > 1
                and isinstance(value[-1], (Promise, str))
            ):
                *value, label = value
                value = tuple(value)
            else:
                label = key.replace("_", " ").title()
            labels.append(label)
            # Use dict.__setitem__() to suppress defenses against double
            # assignment in enum's classdict.
            dict.__setitem__(classdict, key, value)
        cls = super().__new__(metacls, classname, bases, classdict, **kwds)
        member_values: ValuesView[Choices] = cls.__members__.values()
        for member, label in zip(member_values, labels, strict=False):
            member._label_ = label
        return enum.unique(cls)  # type:ignore[type-var]

    if TYPE_CHECKING:

        def __iter__(self) -> Iterator["Choices"]: ...  # type:ignore[override]

    @property
    def names(cls) -> list[str]:
        empty = ["__empty__"] if hasattr(cls, "__empty__") else []
        return empty + [member.name for member in cls]

    @property
    def choices(cls) -> list[tuple[Any, str]]:
        empty = [(None, cls.__empty__)] if hasattr(cls, "__empty__") else []
        return empty + [(member.value, member.label) for member in cls]

    @property
    def labels(cls) -> list[str]:
        return [label for _, label in cls.choices]

    @property
    def values(cls) -> list[Any]:
        return [value for value, _ in cls.choices]


class Choices(enum.Enum, metaclass=ChoicesType):
    """Class for creating enumerated choices."""

    do_not_call_in_templates = enum.nonmember(True)
    _label_: str

    @enum_property
    def label(self) -> str:
        return self._label_

    # A similar format was proposed for Python 3.10.
    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}.{self._name_}"


class IntegerChoices(Choices, IntEnum):
    """Class for creating enumerated integer choices."""

    if TYPE_CHECKING:

        def __iter__(self) -> list[int]: ...

        @property
        def values(cls) -> list[int]: ...

        @enum_property
        def value(self) -> int: ...


class TextChoices(Choices, StrEnum):
    """Class for creating enumerated string choices."""

    @staticmethod
    def _generate_next_value_(name: str, start, count, last_values) -> str:
        return name
