from __future__ import annotations

from enum import auto
from pathlib import Path
from typing import get_type_hints

import pytest

from asynctor.compat import Self, StrEnum, load_toml


class PeopleEnum(StrEnum):
    man = "男"
    female = "女"
    other = "其他"


class AutoEnum(StrEnum):
    First = auto()
    second = auto()
    THIRD = auto()
    fOur = auto()
    five_ = auto()
    _six = auto()


def test_chdir(tmp_work_dir):
    assert tmp_work_dir == Path.cwd()


def test_strenum():
    assert PeopleEnum.man == "男"
    assert PeopleEnum.man is not "男"
    assert PeopleEnum.man.value == "男"
    assert list(PeopleEnum) == [PeopleEnum.man, PeopleEnum.female, PeopleEnum.other]
    assert str(PeopleEnum.man) == "男"
    assert repr(PeopleEnum.man) == "<PeopleEnum.man: '男'>"
    assert [i.value for i in AutoEnum] == ["first", "second", "third", "four", "five_", "_six"]
    with pytest.raises(AttributeError):
        AutoEnum.__seven  # type:ignore
    with pytest.raises(TypeError, match="1 is not a string"):

        class A(StrEnum):
            a = 1

    with pytest.raises(TypeError):

        class B(StrEnum):
            a = "a", 1

    with pytest.raises(TypeError):

        class C(StrEnum):
            a = "a", "b", 1

    with pytest.raises(TypeError):

        class D(StrEnum):
            a = "a", "b", "c", "d"

    class E(StrEnum):
        a = b"a", "utf-8"

    assert E.a == "a"

    class F(StrEnum):
        a = "哈喽".encode(), "ascii", "ignore"
        b = "哈喽".encode(), "gbk", "ignore"
        c = "哈喽".encode("gbk"), "gbk", "ignore"

    assert F.a == ""
    assert F.b == "鍝堝柦"
    assert F.c == "哈喽"


def test_load_toml():
    file = Path(__file__).parent.parent / "pyproject.toml"
    content = file.read_text("utf-8")
    assert load_toml(content)["project"]["name"] == "asynctor"


def test_self():
    class A:
        def a_self(self) -> Self:  # Got right type annotation for sub class
            return self

        def a_class(self) -> A:  # Got error type annotation for sub class
            return self

    class B(A):
        _b: str = "B"

    self_b = B().a_self()._b
    class_b = B().a_class()._b  # type:ignore[attr-defined]
    assert self_b == class_b == "B"

    assert get_type_hints(B().a_self)["return"] is Self
    with pytest.raises(NameError):
        (get_type_hints(B().a_class))
