from __future__ import annotations

import functools
import inspect
import sys
import time
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
)
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    TypeVar,
    overload,
)

if TYPE_CHECKING:  # pragma: no cover
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

T_Retval = TypeVar("T_Retval", Awaitable[Any], Any)


class Timer(AbstractContextManager, AbstractAsyncContextManager):
    """Print time cost of the function.

    Usage::
        >>> @Timer
        >>> async def main():
        ...     # ... async code or sync code ...

        >>> @Timer
        >>> def read_text(filename):
        ...     from pathlib import Path
        ...     return Path(filename).read_text()

        >>> with Timer('do sth ...'):
        ...     # ... sync code ...

        >>> async with Timer('do sth ...'):
        ...     # ... async code ...
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

    async def __aenter__(self) -> "Timer":
        return self.__enter__()

    async def __aexit__(self, *args, **kwargs) -> None:
        self.__exit__(*args, **kwargs)

    def __enter__(self) -> "Self":
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

    def _recreate_cm(self) -> "Self":
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
        >>> @timeit
        >>> async def main():
        ...     # ... async code ...

        >>> @timeit
        >>> def read_text(filename):
        ...     from pathlib import Path
        ...     return Path(filename).read_text()
        >>> args, kwargs = (), {}
        >>> def sync_func(): ...
        >>> res = timeit(sync_func)(*args, **kwargs)
        >>> async def async_func(): ...
        >>> result = await timeit(async_func)(*args, **kwargs)
        >>> with timeit('message'):
        ...     await main()

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
