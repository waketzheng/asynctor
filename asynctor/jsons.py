from __future__ import annotations

import functools
from typing import Any, Callable

try:
    import orjson
except ImportError:
    import json

    def json_dumps(
        obj: Any, default: Callable[[Any], Any] | None = None, *, pretty: bool = False
    ) -> str:
        dumps = functools.partial(json.dumps, obj, default=default)
        return dumps(indent=2, ensure_ascii=False) if pretty else dumps(separators=(",", ":"))

    def json_dump_bytes(
        obj: Any, default: Callable[[Any], Any] | None = None, *, pretty: bool = False
    ) -> bytes:
        return json_dumps(obj, pretty=pretty, default=default).encode()

    def json_loads(
        obj: str | bytes | bytearray,
    ) -> dict[str, Any] | list[Any] | str | bool | int | float | None:
        return json.loads(obj)
else:

    def json_dump_bytes(
        obj: Any, default: Callable[[Any], Any] | None = None, *, pretty: bool = False
    ) -> bytes:
        option = orjson.OPT_INDENT_2 if pretty else None
        return orjson.dumps(obj, option=option, default=default)

    def json_dumps(
        obj: Any, default: Callable[[Any], Any] | None = None, *, pretty: bool = False
    ) -> str:
        return json_dump_bytes(obj, pretty=pretty, default=default).decode()

    def json_loads(
        obj: str | bytes | bytearray,
    ) -> dict[str, Any] | list[Any] | str | bool | int | float | None:
        return orjson.loads(obj)


json_dump_bytes.__doc__ = """Serialize ``obj`` to a JSON formatted bytes

:param obj: object to be dumped
:param default: a function that return a serializable version of obj or raise TypeError
:param pretty: whether indent to humanize
"""
json_dumps.__doc__ = """Serialize ``obj`` to a JSON formatted string

:param obj: object to be dumped
:param default: a function that return a serializable version of obj or raise TypeError
:param pretty: whether indent to humanize
"""
json_loads.__doc__ = """Deserialize JSON to Python objects."""
