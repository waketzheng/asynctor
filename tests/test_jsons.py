import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from asynctor.exceptions import AsynctorError, UnsupportedError
from asynctor.jsons import FastJson, json_dump_bytes, json_dumps, json_loads


def default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def test_dumps():
    assert json_dumps({1: 1}) == '{"1":1}'
    assert json_dumps({1: 1}, pretty=True) == '{\n  "1": 1\n}'
    dt = datetime(2025, 11, 13)
    assert json_dumps({1: dt}) == '{"1":"2025-11-13T00:00:00"}'
    dc = Decimal(0)
    with pytest.raises(TypeError):
        json_dumps({1: dc})
    assert json_dumps({1: dc}, default=default) == '{"1":0.0}'


def test_dump_bytes():
    assert json_dump_bytes({1: 1}) == b'{"1":1}'
    assert json_dump_bytes({1: 1}, pretty=True) == b'{\n  "1": 1\n}'


def test_loads():
    assert json_loads(b'{"1":1}') == {"1": 1}
    assert json_loads('{"1":1}') == {"1": 1}


def test_fast_json():
    assert FastJson.loads(b'{"1":1}') == {"1": 1}
    assert FastJson.loads.__doc__ == json_loads.__doc__
    assert FastJson.dumps({1: 1}, "str") == '{"1":1}'
    assert FastJson.dumps({1: 1}, "string") == '{"1":1}'  # type:ignore
    assert FastJson.dumps({1: 1}, output="str") == '{"1":1}'
    assert FastJson.dumps({1: 1}, output=str) == '{"1":1}'  # type:ignore
    assert FastJson.dumps({1: 1}, "str", pretty=True) == '{\n  "1": 1\n}'
    assert FastJson.dumps({1: 1}, pretty=True, output="str") == '{\n  "1": 1\n}'
    assert FastJson.dumps({1: 1}) == b'{"1":1}'
    assert FastJson.dumps({1: 1}, "bytes") == b'{"1":1}'
    assert FastJson.dumps({1: 1}, output="bytes") == b'{"1":1}'
    assert FastJson.dumps({1: 1}, pretty=True) == b'{\n  "1": 1\n}'
    assert FastJson.dumps({1: 1}, "str") == '{"1":1}'
    dt = datetime(2025, 11, 13)
    assert FastJson.dumps({1: dt}) == b'{"1":"2025-11-13T00:00:00"}'
    dc = Decimal(0)
    with pytest.raises(TypeError):
        FastJson.dumps({1: dc})
    # For `default` case, use `json_dumps` or `json_dump_bytes` instead
    with pytest.raises(
        TypeError, match=re.escape("FastJson.dumps() got an unexpected keyword argument 'default'")
    ):
        FastJson.dumps({1: dc}, default=default)  # type:ignore


def test_fast_json_unsupported_output():
    with pytest.raises(ValueError):
        FastJson.dumps({1: 1}, output=bytes)  # type:ignore
    with pytest.raises(AsynctorError):
        FastJson.dumps({1: 1}, output=bytes)  # type:ignore
    with pytest.raises(UnsupportedError):
        FastJson.dumps({1: 1}, output=bytes)  # type:ignore


def test_fast_json_write(tmp_work_dir):
    p = Path("a.json")
    assert FastJson.dumps({1: 1}, p) == b'{"1":1}'
    assert p.read_bytes() == b'{"1":1}'
    assert FastJson.dumps({1: 1}, p, pretty=True) == b'{\n  "1": 1\n}'
    assert p.read_bytes() == b'{\n  "1": 1\n}'
    assert FastJson.dumps({1: 1}, pretty=True, output=p) == b'{\n  "1": 1\n}'
