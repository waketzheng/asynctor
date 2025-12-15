import sys
from enum import auto

import pytest

if sys.version_info >= (3, 11):
    from asynctor.enums import IntegerChoices, TextChoices
else:
    from enum import Enum as IntegerChoices
    from enum import Enum as TextChoices


class DirectionChoices(IntegerChoices):
    dong = 0, "East"
    nan = 1, "South"
    xi = 2, "West"
    bei = 3, "North"


def name_to_label(name: str, enum_type=DirectionChoices) -> str:
    return enum_type[name].label


def value_to_label(value: int, enum_type=DirectionChoices) -> str:
    return enum_type(value).label


def label_to_value(label: str, enum_type=DirectionChoices) -> int:
    return {v: k for k, v in enum_type.choices}[label]


@pytest.mark.skipif(
    sys.version_info < (3, 11), reason="IntegerChoices requires python3.11 or higher"
)
def test_int():
    assert DirectionChoices.dong == 0
    assert DirectionChoices.dong is not 0  # NOQA
    assert DirectionChoices.dong.value == 0
    assert str(DirectionChoices.dong) == "0"
    assert repr(DirectionChoices.dong) == "DirectionChoices.dong"
    assert list(DirectionChoices) == [0, 1, 2, 3]
    assert DirectionChoices.values == [0, 1, 2, 3]
    assert DirectionChoices.names == ["dong", "nan", "xi", "bei"]
    assert DirectionChoices.labels == ["East", "South", "West", "North"]
    assert DirectionChoices.choices == [(0, "East"), (1, "South"), (2, "West"), (3, "North")]
    assert DirectionChoices[DirectionChoices.xi.name] == DirectionChoices.xi
    assert DirectionChoices(DirectionChoices.xi.value) == DirectionChoices.xi
    assert dict(zip(DirectionChoices.names, DirectionChoices.labels, strict=False)) == {
        "dong": "East",
        "nan": "South",
        "xi": "West",
        "bei": "North",
    }
    assert name_to_label("nan") == "South"
    assert value_to_label(1) == "South"
    assert label_to_value("South") == 1


class BoolEnum(TextChoices):
    yes = "true", "True"
    no = "false", "False"


class AutoName(TextChoices):
    aBc = auto()
    a_1 = auto()
    b__2 = auto()
    c_d_e = auto()
    HELLO = auto()
    world = auto()
    good_luck = auto()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="TextChoices requires python3.11 or higher")
def test_str():
    assert BoolEnum.no == "false"
    assert str(BoolEnum.no) == "false"
    assert BoolEnum.no.label == "False"
    assert list(BoolEnum) == ["true", "false"]
    assert name_to_label("yes", BoolEnum) == "True"
    assert value_to_label("true", BoolEnum) == "True"  # type:ignore
    assert label_to_value("True", BoolEnum) == "true"
    assert BoolEnum.choices == [("true", "True"), ("false", "False")]
    # test auto
    assert AutoName.choices == [
        ("aBc", "Abc"),
        ("a_1", "A 1"),
        ("b__2", "B  2"),
        ("c_d_e", "C D E"),
        ("HELLO", "Hello"),
        ("world", "World"),
        ("good_luck", "Good Luck"),
    ]
