import sys

if sys.version_info >= (3, 10):  # pragma: no cover
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias


__all__ = ("TypeAlias",)
