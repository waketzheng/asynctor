from asynctor.jsons import json_dump_bytes, json_dumps, json_loads


def test_dumps():
    assert json_dumps({1: 1}) == '{"1":1}'
    assert json_dumps({1: 1}, pretty=True) == '{\n  "1": 1\n}'


def test_dump_bytes():
    assert json_dump_bytes({1: 1}) == b'{"1":1}'


def test_loads():
    assert json_loads(b'{"1":1}') == {"1": 1}
    assert json_loads('{"1":1}') == {"1": 1}
