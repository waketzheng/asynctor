from __future__ import annotations

import functools
from collections.abc import Callable
from datetime import date, datetime, time
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
        dumps = functools.partial(json.dumps, default=default)
        if pretty:
            dumps = functools.partial(dumps, indent=2, ensure_ascii=False)
        else:
            dumps = functools.partial(dumps, separators=(",", ":"))
        try:
            return dumps(obj)
        except TypeError as e:
            if str(e) not in (
                "keys must be str, int, float, bool or None, not datetime.datetime",
                "keys must be str, int, float, bool or None, not datetime.date",
                "keys must be str, int, float, bool or None, not datetime.time",
                "Object of type datetime is not JSON serializable",
                "Object of type date is not JSON serializable",
                "Object of type time is not JSON serializable",
            ):
                raise

            class DateTimeDecoder(json.JSONEncoder):
                @staticmethod
                def time_serializer(obj: Any) -> Any:
                    if isinstance(obj, (datetime, date, time)):
                        return str(obj).replace(" ", "T")
                    return obj

                def default(self, obj) -> Any:
                    obj = self.time_serializer(obj)
                    return super().default(obj)

                def encode(self, obj):
                    # Convert datetime keys to strings
                    def convert_keys(item):
                        if isinstance(item, dict):
                            return {
                                self.time_serializer(k): convert_keys(v) for k, v in item.items()
                            }
                        elif isinstance(item, list | tuple):
                            return [convert_keys(i) for i in item]
                        else:
                            return self.time_serializer(item)

                    converted = convert_keys(obj)
                    return super().encode(converted)

            return dumps(obj, cls=DateTimeDecoder)

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
        option = orjson.OPT_NON_STR_KEYS
        if pretty:
            option |= orjson.OPT_INDENT_2
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
