from __future__ import annotations

import functools
import os
import shlex
import socket
import subprocess  # nosec
import sys
import warnings
from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, AbstractContextManager, asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

if TYPE_CHECKING:
    from types import TracebackType

    from asgi_lifespan._types import ASGIApp
    from fastapi import FastAPI

    from . import testing
    from .compat import Self
    from .testing import AsyncClient


T = TypeVar("T")
AsyncClientGenerator: TypeAlias = AsyncGenerator["AsyncClient"]


def _deprecated_warns(name: str) -> None:
    msg = "Using `asynctor.utils.{0}` is deprecated; use `asynctor.testing.{0}` instead."
    warnings.warn(
        msg.format(name),
        DeprecationWarning,
        stacklevel=2,
    )


@asynccontextmanager
async def client_manager(
    app: FastAPI,
    base_url: str = "http://test",
    mount_lifespan: bool = True,
    timeout: int | float = 30,
    **kwargs,
) -> AsyncClientGenerator:
    """
    Deprecated! Use `asynctor.testing.client_manager` instead.
    """
    from asynctor.testing import client_manager as _client_manager

    _deprecated_warns("client_manager")
    async with _client_manager(app, base_url, mount_lifespan, timeout, **kwargs) as c:
        yield c


class AsyncTestClient(AbstractAsyncContextManager):
    """
    Deprecated! Use `asynctor.testing.AsyncTestClient` instead.
    """

    @property
    def client_cls(self) -> type[testing.AsyncTestClient]:
        from asynctor.testing import AsyncTestClient as _AsyncTestClient

        return _AsyncTestClient

    def __init__(self, *args, **kwargs) -> None:
        _deprecated_warns("AsyncTestClient")
        self.client_cls.__init__(self, *args, **kwargs)  # type:ignore

    async def __aenter__(self) -> AsyncClient:
        await self.client_cls.__aenter__(self)  # type:ignore
        return self._client  # type:ignore

    async def _init_app(self) -> ASGIApp:
        return await self.client_cls._init_app(self)  # type:ignore

    async def __aexit__(self, *args, **kw) -> None:
        await self.client_cls.__aexit__(self, *args, **kw)  # type: ignore


def local_dict(data: dict[str, T], *keys: str) -> dict[str, T]:
    """
    Build dict by key from keys, value from data; if key not in data, raise KeyError

    Usage::
        >>> a, b = 1, 2
        >>> local_dict(locals(), 'a', 'b')
        {'a': 1, 'b': 2}

    """
    return {k: data[k] for k in keys}


class AttrDict(dict):
    """Support get dict value by attribution

    NOTE: mypy will complaint attr-defined when using this class, e.g.:
    `error: "AttrDict" has no attribute "a"  [attr-defined]`

    Usage::
        >>> d = AttrDict({'a': 1, 'b': {'c': 2, 'd': {'e': 3}}})
        >>> d.a == d['a'] == 1
        True
        >>> d.b.c == d['b']['c'] == 2
        True
        >>> d.b.d == d['b']['d'] == {'e': 3}
        True
        >>> d.b.d.e == d['b']['d']['e'] == 3
        True
        >>> dd = AttrDict({'keys': 2}, items=1)
        >>> list(dd.items()) == [('keys', 2), ('items', 1)]
        True
        >>> dd['items'] == 1
        True
        >>> list(dd.keys()) == ['keys', 'items']
        True
        >>> dd['keys'] == 2
        True
        >>> d3 = AttrDict({b'a': 1})
        >>> d3[b'a'] == 1 and getattr(d3, 'a', None) is None
        True
    """

    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, **kw)
        exclude = set(dir(self)) | set(self.__dict__)
        for k, v in self.items():
            if not isinstance(k, str) or k in exclude:
                continue
            if isinstance(v, dict):
                v = self.__class__(v)
            self.__dict__.setdefault(k, v)

    def __str__(self) -> str:
        return super().__repr__()

    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + super().__repr__() + ")"


def get_machine_ip() -> str:
    r"""Get IP of current machine by socket, if failed, return '127.0.0.1'

    Usage::
        >>> import re
        >>> my_ip = get_machine_ip()
        >>> bool(re.search(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', my_ip))
        True
        >>> inets = my_ip.split('.')
        >>> len(inets) == 4
        True
        >>> sum(map(lambda x: 0 <= int(x) <= 255, inets))
        4
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(("10.254.254.254", 1))
            return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"


def cache_attr(func: Callable[..., T]) -> Callable[..., T]:
    """Cache result to class attribute

    Usage::
    ```py
    class A:
        @classmethod
        @cache_attr
        def do_sth(cls):
            ...

    result = A.do_sth()
    ```

    Example::
        >>> import time
        >>> from datetime import datetime
        >>> class A:
        ...     @classmethod
        ...     @cache_attr
        ...     def now(cls) -> datetime:
        ...         return datetime.now()
        >>> now_a = A.now()
        >>> time.sleep(0.1)
        >>> now = datetime.now()
        >>> A.now() == now_a == getattr(A, '-cache-now')
        True
        >>> A.now() < now
        True

    """

    @functools.wraps(func)
    def run(cls) -> T:
        key = "-cache-" + getattr(func, "__name__", str(func))
        if hasattr(cls, key):
            return getattr(cls, key)
        res = func(cls)
        setattr(cls, key, res)
        return res

    return run


class Shell:
    """Run shell command by subprocess

    Usage::
        >>> import sys
        >>> s = Shell('python -V')
        >>> r = s.run()
        >>> r.returncode == s.call() == 0
        True
        >>> '{}.{}.{}'.format(*sys.version_info) in s.capture_output()
        True
        >>> code = "import sys;sys.exit(1)"
        >>> Shell(f'python -c {code!r}').call() == 1
        True
    """

    @staticmethod
    def expand_user(cs: list[str]) -> None:
        if cs[0] == "echo":
            return
        for i, c in enumerate(cs):
            if c.startswith("~"):
                cs[i] = os.path.expanduser(c)

    @staticmethod
    def shell_should_be_true(command: list[str] | str) -> bool:
        return bool(set(command) & {"|", ">", "&"})

    @classmethod
    def run_by_subprocess(cls, cmd: str, **kw) -> subprocess.CompletedProcess[str]:
        if (shell := kw.get("shell")) is None and cls.shell_should_be_true(cmd):
            kw["shell"] = shell = True
        command = cmd if shell else shlex.split(cmd)
        return subprocess.run(command, **kw)  # nosec

    @classmethod
    def run_and_echo(
        cls, cmd: str | list[str], *, dry: bool = False, verbose: bool = True, **kw: Any
    ) -> int:
        self = cls(cmd, **kw)
        if dry:
            print("-->", self.command)
            return 0
        return self.call(verbose=verbose)

    def __init__(self, command: list[str] | str, **kwargs) -> None:
        self._command = command
        self._kwargs = kwargs

    @property
    def command(self) -> str:
        if isinstance(self._command, str):
            return self._command
        return " ".join(repr(i) if " " in i else i for i in self._command)

    def run(
        self, kwargs: dict[str, Any] | None = None, *, verbose: bool = False, **kw: Any
    ) -> subprocess.CompletedProcess[str]:
        cmd = self.command
        if verbose:
            print("-->", cmd)
        kwargs = {**(self._kwargs if kwargs is None else kwargs), **kw}
        if kwargs.get("shell") is None and self.shell_should_be_true(self._command):
            kwargs["shell"] = True
        elif isinstance(self._command, list):
            return subprocess.run(self._command, **kwargs)  # nosec
        return self.run_by_subprocess(cmd, **kwargs)

    def call(self, *, verbose: bool = False) -> int:
        return self.run(verbose=verbose).returncode

    def capture_output(self, *, verbose: bool = False) -> str:
        kw = dict(self._kwargs, text=True, encoding="utf-8", capture_output=True)
        r = self.run(kw, verbose=verbose)
        return r.stdout or r.stderr or ""


def load_bool(env: str, *, strict: bool = False) -> bool:
    match os.getenv(env):
        case None:
            return False
        case "1":
            return True
        case "0":
            return False
        case x if x.lower() in ("true", "yes", "on", "y"):
            return True
        case _ as x:
            if strict and x.lower() not in ("false", "no", "off", "n"):
                raise ValueError(f"Value of env {env!r} must be a bool (Got {x!r})")
            return False


class ExtendSyspath(AbstractContextManager):
    """Extend sys.path

    Example::

        from asynctor.utils import ExtendSyspath

        with ExtendSyspath(__file__):
            from app import __version__

    Or:
        from pathlib import Path

        with ExtendSyspath(BASE_DIR := Path(__file__).parent.parent):
            from app import __version__

    """

    def __init__(
        self, path: Path | str | None = None, rollback: bool = False, insert: bool = False
    ) -> None:
        if path is None:
            path = Path()
        elif isinstance(path, str):
            path = Path(path)
        self.path: Path = path
        self._path = ""
        self.rollback = rollback
        self._insert = insert

    def __enter__(self) -> Self:
        if (path := self.path).is_file():
            path = path.parent
        if (p := path.as_posix()) not in sys.path:
            self._path = p
            if self._insert:
                sys.path.insert(0, p)
            else:
                sys.path.append(p)
        elif self._insert and sys.path[0] != p:
            self._path = p
            sys.path.insert(0, p)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.rollback and self._path:
            try:
                index = sys.path.index(self._path)
            except ValueError:
                ...
            else:
                sys.path.pop(index)


def _test() -> None:  # pragma: no cover
    import doctest

    doctest.testmod(verbose=True)


if __name__ == "__main__":
    _test()
