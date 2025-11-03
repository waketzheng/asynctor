"""
This module is for those that support both (python >=3.9,<3.11) and (python >= 3.11)
"""

from __future__ import annotations

import os
import sys
import warnings
from typing import Any

__all__ = ("chdir", "StrEnum", "load_toml", "NotRequired", "Self")

if sys.version_info >= (3, 11):
    from contextlib import chdir
    from enum import StrEnum
    from typing import NotRequired, Self

    from tomllib import loads as load_toml
else:
    import contextlib
    from enum import Enum

    from typing_extensions import NotRequired, Self

    def load_toml(content: str) -> dict[str, Any]:
        try:
            import tomli
        except ImportError:
            tip = (
                "tomli is required for Python<3.11, you can install it by:"
                "\n\n  pip install tomli"
                '\n\nOr:\n\n  pip install "asynctor[toml]"\n'
            )
            warnings.warn(tip, stacklevel=2)
            raise

        return tomli.loads(content)

    class chdir(contextlib.AbstractContextManager):  # Copied from source code of Python3.13
        """Non thread-safe context manager to change the current working directory."""

        def __init__(self, path):
            self.path = path
            self._old_cwd = []

        def __enter__(self):
            self._old_cwd.append(os.getcwd())
            os.chdir(self.path)

        def __exit__(self, *excinfo):
            os.chdir(self._old_cwd.pop())

    # Copied from source code of Python3.14
    class ReprEnum(Enum):
        """
        Only changes the repr(), leaving str() and format() to the mixed-in type.
        """

    class StrEnum(str, ReprEnum):
        """
        Enum where members are also (and must be) strings
        """

        def __new__(cls, *values):
            "values must already be of type `str`"
            if len(values) > 3:
                raise TypeError("too many arguments for str(): %r" % (values,))
            if len(values) == 1:
                # it must be a string
                if not isinstance(values[0], str):
                    raise TypeError("%r is not a string" % (values[0],))
            if len(values) >= 2:
                # check that encoding argument is a string
                if not isinstance(values[1], str):
                    raise TypeError("encoding must be a string, not %r" % (values[1],))
            if len(values) == 3:
                # check that errors argument is a string
                if not isinstance(values[2], str):
                    raise TypeError("errors must be a string, not %r" % (values[2]))
            value = str(*values)
            member = str.__new__(cls, value)
            member._value_ = value
            return member

        @staticmethod
        def _generate_next_value_(name, start, count, last_values):
            """
            Return the lower-cased version of the member name.
            """
            return name.lower()

        __str__ = str.__str__
