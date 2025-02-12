from __future__ import annotations

import functools
import inspect
import sys
import time
from collections.abc import Awaitable, Callable
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
)
from types import TracebackType
from typing import TYPE_CHECKING, Any, TypeVar, overload

if TYPE_CHECKING:  # pragma: no cover
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

T_Retval = TypeVar("T_Retval", Awaitable[Any], Any)


class Timer(AbstractContextManager, AbstractAsyncContextManager):
    """Print time cost of the function.

    Usage::

    ... code-block:: python3

        import time
        from loguru import logger

        def do_staff():
            time.sleep(0.1)

        with Timer('do sth ...'):
            do_staff()
        # do sth ... Cost: 0.1 seconds

        with Timer('do sth ...', verbose=False) as t:
            do_staff()
        assert isinstance(t.cost, float)
        logger.info(str(t))
        # do sth ... Cost: 0.1 seconds

        @Timer
        async def main():
            do_staff()

        await main()
        # main Cost: 0.1 seconds

        @Timer
        def read_text(filename):
            from pathlib import Path
            time.sleep(0.2222)
            return Path(filename).read_text()

        read_text('a.txt')
        # read_text Cost: 0.2 seconds
    """

    def __init__(self, message: str | Callable, decimal_places=1, verbose=True) -> None:
        if callable(message):  # Use as decorator
            func = message
            self.__name__ = message = func.__name__
            self.func: Callable = func
        self.message = message
        self._decimal_places = decimal_places
        self._end = self._start = time.time()
        self._verbose = verbose

    def start(self) -> None:
        self._start = time.time()

    def capture(self, verbose=None) -> None:
        self._end = time.time()
        if verbose is None:
            verbose = self._verbose
        if verbose:
            print(self)

    @property
    def cost(self) -> float:
        return round(self._end - self._start, self._decimal_places)

    def __str__(self) -> str:
        return f"{self.message} Cost: {self.cost} seconds"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.message!r}, {self._decimal_places}, {self._verbose})"

    async def __aenter__(self) -> Timer:
        return self.__enter__()

    async def __aexit__(self, *args, **kwargs) -> None:
        self.__exit__(*args, **kwargs)

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not SystemExit or not str(exc_val):
            self.capture()

    def _recreate_cm(self) -> Self:
        return self.__class__(
            getattr(self, "func", None) or self.message,
            self._decimal_places,
            self._verbose,
        )

    def __call__(self, *args, **kwargs) -> Any:
        if (func := getattr(self, "func", None)) is None:
            return None
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def inner(*gs, **kw):
                async with self._recreate_cm():
                    return await func(*gs, **kw)

            return inner(*args, **kwargs)
        else:
            with self._recreate_cm():
                return func(*args, **kwargs)


@overload
def timeit(func: str) -> Timer: ...  # pragma: no cover


@overload
def timeit(
    func: Callable[..., T_Retval],
) -> Callable[..., T_Retval]: ...  # pragma: no cover


def timeit(func: str | Callable[..., T_Retval]) -> Timer | Callable[..., T_Retval]:
    """Print time cost of the function.

    Usage::

    ... code-block:: python3

        import anyio, time

        @timeit
        async def main():
            await anyio.sleep(0.1)

        await main()
        # main Cost: 0.1 seconds

        @timeit
        def read_text(filename):
            from pathlib import Path
            time.sleep(0.25)
            return Path(filename).read_text()

        read_text('a.txt')
        # read_text Cost: 0.2 seconds

        args, kwargs = (), {}
        def sync_func(): time.sleep(0.24)
        res = timeit(sync_func)(*args, **kwargs)
        # sync_func Cost: 0.2 seconds

        async def async_func():
            await anyio.sleep(1)
        result = await timeit(async_func)(*args, **kwargs)
        # async_func Cost: 1.0 seconds

        with timeit('message'):
            await async_func()
        # message Cost: 1.0 seconds

    """
    if isinstance(func, str):
        return Timer(func)
    func_name = getattr(func, "__name__", str(func))
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def deco(*args, **kwargs) -> T_Retval:
            async with Timer(func_name):
                return await func(*args, **kwargs)

    else:

        @functools.wraps(func)
        def deco(*args, **kwargs) -> T_Retval:
            with Timer(func_name):
                return func(*args, **kwargs)

    return deco
