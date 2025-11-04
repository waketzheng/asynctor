from __future__ import annotations

import functools
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, TypeAlias, overload

from .exceptions import UnsupportedError

BasicJsonType: TypeAlias = str | bool | int | float | None
JsonAbleType: TypeAlias = dict[str, Any] | list[Any] | BasicJsonType
StrictJsonType: TypeAlias = dict[str, JsonAbleType] | list[JsonAbleType] | BasicJsonType
DumpedJsonType: TypeAlias = str | bytes | bytearray

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

    def json_loads(obj: DumpedJsonType) -> JsonAbleType:
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

    def json_loads(obj: DumpedJsonType) -> JsonAbleType:
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


class FastJson:
    @overload
    @classmethod
    def dumps(cls, obj: Any, output: Literal["str"], *, pretty: bool = False) -> str: ...
    @overload
    @classmethod
    def dumps(
        cls, obj: Any, output: Literal["bytes"] | Path = "bytes", *, pretty: bool = False
    ) -> bytes: ...

    @classmethod
    def dumps(
        cls,
        obj: Any,
        output: Literal["str", "bytes"] | Path = "bytes",
        *,
        pretty: bool = False,
    ) -> str | bytes:
        """Serialize ``obj`` to a JSON formatted string or bytes

        :param obj: object to be dumped.
        :param output: if 'str' return utf-8 string, elif 'bytes' return utf-8 encoded bytes,
                    elif Path write dumped content to it and return bytes, else raise ValueError.
        :param pretty: whether indent to humanize.
        """
        match output:
            case "bytes" | Path():
                content = json_dump_bytes(obj, pretty=pretty)
                if isinstance(output, Path):
                    output.write_bytes(content)
                return content
            case "str" | "string":
                return json_dumps(obj, pretty=pretty)
            case x if x is str:  # support: FastJson.dumps(obj, output=str)
                return json_dumps(obj, pretty=pretty)
            case _:
                raise UnsupportedError(f"Unsupported output format: {output!r}")

    loads = staticmethod(json_loads)
