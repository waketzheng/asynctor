# mypy: disable-error-code="attr-defined"
import pytest

from asynctor import AttrDict
from asynctor.utils import get_machine_ip


class TestAttrDict:
    def test_normal_case(self):
        origin_dict = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
        d = AttrDict(origin_dict)
        assert d == origin_dict
        assert d.a == d["a"] == 1
        assert d.b == d["b"] == {"c": 2, "d": {"e": 3}}
        assert d.b.c == d["b"]["c"] == 2
        assert d.b.d == d["b"]["d"] == {"e": 3}
        assert d.b.d.e == d["b"]["d"]["e"] == 3
        assert str(d) == str(origin_dict)
        assert repr(d) == "AttrDict(" + repr(origin_dict) + ")"

    def test_raises(self):
        with pytest.raises(AttributeError):
            assert AttrDict().a
        with pytest.raises(KeyError):
            assert AttrDict()["a"]

    def test_key_startswith_underline(self):
        d = AttrDict({"_a": 1, "__b": 2, "___c": 3, "____d": 4})
        assert d._a == d["_a"] == 1
        assert d["__b"] == 2
        assert d["___c"] == 3
        assert d["____d"] == 4
        with pytest.raises(AttributeError):
            assert d.__b
        with pytest.raises(AttributeError):
            assert d.___c
        with pytest.raises(AttributeError):
            assert d.____d

    def test_initial(self):
        assert AttrDict() == {} == dict()
        assert AttrDict(a=1) == {"a": 1} == dict(a=1)
        assert AttrDict(a=1, b=2) == {"a": 1, "b": 2} == dict(a=1, b=2)
        assert (
            AttrDict({1: 2}, a=1, b=2)
            == {1: 2, "a": 1, "b": 2}
            == dict({1: 2}, a=1, b=2)  # type:ignore[dict-item]
        )
        assert AttrDict({1: 0}, a=1, b=2, **{"c": 3}) == {1: 0, "a": 1, "b": 2, "c": 3}

    def test_origin_attrs(self):
        d = AttrDict()
        attrs = [i for i in dir(dict) if not i.startswith("__")]
        for index, attr in enumerate(attrs):
            assert callable(getattr(d, attr))
            d[attr] = index
            assert d[attr] == index
            assert callable(getattr(d, attr))

    def test_string_keys_that_can_not_be_attribution(self):
        d = AttrDict({"a-b": 1, ("a", "b"): 2, None: 3, "c_d": 4, "e f": 5})
        assert d["a-b"] == 1
        assert d[("a", "b")] == 2
        with pytest.raises(AttributeError):
            assert d.a_b
        with pytest.raises(AttributeError):
            assert d.ab
        assert d["c_d"] == d.c_d == 4
        assert d["e f"] == 5
        with pytest.raises(AttributeError):
            assert d.e_f
        with pytest.raises(AttributeError):
            assert d.ef


def test_get_ip(mocker):
    my_ip = get_machine_ip()
    nets = my_ip.split(".")
    assert len(nets) == 4
    assert all(0 <= int(i) <= 255 for i in nets)
    mocker.patch("socket.socket.getsockname", return_value=True)
    assert get_machine_ip() == "127.0.0.1"
