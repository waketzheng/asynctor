from __future__ import annotations

import functools
import itertools
import sys
import warnings
from collections.abc import AsyncGenerator, Awaitable, Generator, Iterable, Sequence
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Callable, Literal, TypeVar, cast, overload

import anyio
import sniffio
from anyio import from_thread
from anyio._backends._asyncio import get_running_loop
from anyio.lowlevel import checkpoint

from .exceptions import ParamsError

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import ParamSpec, Self, TypeVarTuple, Unpack
else:
    from exceptiongroup import ExceptionGroup  # pragma: no cover
    from typing_extensions import ParamSpec, Self, TypeVarTuple, Unpack  # pragma: no cover

if TYPE_CHECKING:
    from anyio.abc._tasks import TaskGroup

    from ._types import TypeAlias

T = TypeVar("T")
T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")
PosArgsT = TypeVarTuple("PosArgsT")
AsyncFunc: TypeAlias = Callable[..., Awaitable[Any]]


@overload
def ensure_afunc(
    coro: Awaitable[T_Retval],
) -> Callable[[], Awaitable[T_Retval]]: ...


@overload
def ensure_afunc(
    coro: Callable[T_ParamSpec, Awaitable[T_Retval]],
) -> Callable[T_ParamSpec, Awaitable[T_Retval]]: ...


def ensure_afunc(
    coro: Awaitable[T_Retval] | Callable[T_ParamSpec, Awaitable[T_Retval]],
) -> Callable[[], Awaitable[T_Retval]] | Callable[T_ParamSpec, Awaitable[T_Retval]]:
    """Wrap coroutine to be async function"""
    if callable(coro):
        return coro

    async def do_await() -> T_Retval:
        return await coro

    return do_await


def run(
    func: (Awaitable[T_Retval] | Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]]),
    *args: Unpack[PosArgsT],
    backend: str = "asyncio",
    backend_options: dict[str, Any] | None = None,
) -> T_Retval:
    """Combine `asyncio.run` and `anyio.run`

    :param func: async function or coroutine.
    :param args: arguments that will pass to `func` if it's a function.
    :param backend: should be 'asyncio' or 'trio'.
    :param backend_options: will pass to `anyio.run`.

    Usage::

    ... code-block:: python3

        from functools import partial

        async def foo(a, b, *, c=3):
            return a, b, c

        result_asyncio_format = run(foo(1, 2, c=0))
        result_anyio_format = run(partial(foo, c=0), 1, 2)
        assert result_asyncio_format == result_anyio_format

    """
    if not callable(func):

        async def do_await() -> T_Retval:
            return await func

        return anyio.run(do_await, backend=backend, backend_options=backend_options)
    return anyio.run(func, *args, backend=backend, backend_options=backend_options)


class LengthFixedList(list[T]):
    def append(self: Self, _: T) -> None:
        raise TypeError(f"{self.__class__.__name__} is fixed-size")


async def map_group(
    func: AsyncFunc, todos: Iterable[Any], results: list[Any] | None = None
) -> None:
    """
    The `map_group` function asynchronously executes a given function for each set of arguments in a
    provided iterable using `anyio.create_task_group()`.

    :param func: The `func` parameter is an asynchronous function that will be applied to
        each item in the `todos` iterable
    :param todos: The `todos` parameter in the `map_group` function represents an iterable
        containing the arguments that will be passed to the `func` function for each task
        that is started in the task group. Each element in `todos` is a set of arguments
        that will be unpacked and passed to the `func`.
    :param results: The `results` parameter in the `map_group` function is a list that
        stores the results of the asynchronous function calls.
        If the `results` parameter is provided with an initial list,
        the results of each function call will be appended to this list.
        If `results` is None or not provided, tasks will run without any return.
    """
    async with anyio.create_task_group() as tg:
        should_append = results is not None and not isinstance(results, LengthFixedList)
        for args in todos:
            if should_append:
                cast(list[Any], results).append(None)
            tg.start_soon(func, *args)


@overload
async def bulk_gather(
    coros: Sequence[Awaitable[T_Retval]] | Generator[Awaitable[T_Retval]],
    batch_size: int = 0,
    wait_last: bool = False,
    raises: Literal[True] = True,
    *,
    limit: int | None = None,
) -> tuple[T_Retval, ...]: ...


@overload
async def bulk_gather(
    coros: Sequence[Awaitable[T_Retval]] | Generator[Awaitable[T_Retval]],
    batch_size: int = 0,
    wait_last: bool = False,
    raises: Literal[False] = False,
    *,
    limit: int | None = None,
) -> tuple[T_Retval | None, ...]: ...


async def bulk_gather(
    coros: Sequence[Awaitable[T_Retval]] | Generator[Awaitable[T_Retval]],
    batch_size: int = 0,
    wait_last: bool = False,
    raises: bool = True,
    *,
    limit: int | None = None,
) -> tuple[T_Retval | None, ...]:
    """
    Similar like `asyncio.gather`, but support the `batch_size` parameter.
    If batch_size is not zero, running tasks will CapacityLimiter({batch_size}).

    :param coros: Coroutines
    :param batch_size: running tasks limit number, set 0 to be unlimit.
    :param wait_last: if True, wait last bulk tasks to complete then start new task group,
        else use anyio.CapacityLimiter to limit task number.
    :param raises: if True, raise Exception when coroutine failed, else return None.
    :param limit: (deprecated) only leave it here to compare with old version.
    """
    results: list[T_Retval | None]
    try:
        total = len(coros)  # type:ignore[arg-type]
    except TypeError:  # if coros is generator
        total = 0
        results = []
    else:
        if total == 0:
            await checkpoint()
            return ()
        results = LengthFixedList([None] * total)

    async def runner(_i: int, _coro: Awaitable[T_Retval]) -> None:
        results[_i] = await _coro

    async def limited_runner(
        _i: int, _coro: Awaitable[T_Retval], _limiter: anyio.CapacityLimiter
    ) -> None:
        async with _limiter:
            results[_i] = await _coro

    try:
        if limit is not None:
            if batch_size:
                if batch_size != limit:
                    raise ParamsError(f"Conflict value with {limit=} & {batch_size=}")
                warnings.warn(
                    "`limit` is deprecated, use `batch_size` only.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            else:
                batch_size = limit
        if batch_size:
            if wait_last:
                if total == 0:
                    todos: list[tuple[int, Awaitable[T_Retval]]] = []
                    for count, args in zip(itertools.count(), enumerate(coros)):
                        todos.append(args)
                        results.append(None)
                        if count % batch_size == 0:
                            await map_group(runner, todos)
                            todos.clear()
                    if todos:
                        await map_group(runner, todos)
                else:
                    for start in range(0, total, batch_size):
                        coros_slice = itertools.islice(coros, start, start + batch_size)
                        args_items = ((start + i, coro) for i, coro in enumerate(coros_slice))
                        await map_group(runner, args_items)
            else:
                limiter = anyio.CapacityLimiter(batch_size)
                todo_args = ((*item, limiter) for item in enumerate(coros))
                if total == 0:
                    await map_group(limited_runner, todo_args, results)
                else:
                    await map_group(limited_runner, todo_args)
        else:
            if total == 0:
                await map_group(runner, enumerate(coros), results)
            else:
                await map_group(runner, enumerate(coros))
    except ExceptionGroup as e:
        if raises:
            raise e.exceptions[0] from e

    return tuple(results)


async def gather(*coros: Awaitable[T_Retval], limit: int | None = None) -> tuple[T_Retval, ...]:
    """Similar like asyncio.gather, but support set `limit` to control concurrency number.

    :param coros: Coroutines to be executed in the running loop
    :param limit: How many coroutines will be run in the same time (none or zero is unlimit).
    """
    return await bulk_gather(coros, limit=limit)


def create_task(coro: Awaitable[Any], task_group: TaskGroup, *, name: object = None) -> None:
    """Start an async task, similar to asyncio.create_task, but need a task_group param.

    :param coro: Coroutine that will be run in the backgroup
    :param task_group: The backgroup task group

    Usage::
        >>> async def afunc(): ...
        >>> async with anyio.create_task_group() as tg:
        ...     create_task(afunc(), tg)
    """
    task_group.start_soon(ensure_afunc(coro), name=name)


@asynccontextmanager
async def start_tasks(
    coro: Awaitable[Any] | Callable[..., Awaitable[Any]],
    *more: Awaitable[Any] | Callable[..., Awaitable[Any]],
) -> AsyncGenerator[None]:
    """Make it easy to convert asyncio.create_task

    Usage:

    ... code-block:: python3

        async def startup():
            # cost a long time to do sth async
            await anyio.sleep(1000)

        @contextlib.asynccontextmanager
        async def lifespan(app):
            async with start_tasks(startup()):
                yield
    """
    async with anyio.create_task_group() as tg:
        with anyio.CancelScope(shield=True):
            tg.start_soon(ensure_afunc(coro))
            for c in more:
                tg.start_soon(ensure_afunc(c))
            try:
                yield
            finally:
                tg.cancel_scope.cancel()


async def wait_for(coro: Awaitable[T_Retval], timeout: int | float) -> T_Retval:
    """Similar like asyncio.wait_for"""
    with anyio.fail_after(timeout):
        return await coro


def run_async(
    async_func: Awaitable[T_Retval] | Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]],
    *args: Unpack[PosArgsT],
) -> T_Retval:
    """Run async function in worker thread and get the result of it"""
    # `asyncio.run(async_func())`/`anyio.run(async_func)` can get the result of async function,
    # but both of them will close the running loop.
    result: list[T_Retval] = []

    async def runner() -> None:
        if callable(async_func):
            coro = async_func(*args)
            try:
                res = await coro
            except TypeError as e:
                msg = (
                    "object can't be awaited"
                    if sys.version_info >= (3, 14)
                    else "can't be used in 'await' expression"
                )
                if msg in str(e):
                    # In case of async_func is a sync function
                    res = cast(T_Retval, coro)
                    await checkpoint()
                else:
                    raise
        else:
            res = await async_func
        result.append(res)

    with from_thread.start_blocking_portal() as portal:
        portal.call(runner)

    return result[0]


def async_to_sync(
    func: Callable[T_ParamSpec, Awaitable[T_Retval]],
) -> Callable[T_ParamSpec, T_Retval]:
    """Run async function to be sync.

    If there is a running loop, try to run in it,
    otherwise run in worker thread with new loop

    Usage::
        >>> async def do_sth():
        ...     await anyio.sleep(0.1)
        ...     return 1
        >>> res = async_to_sync(do_sth)()
        >>> assert res == 1
    """

    @functools.wraps(func)
    def runner(*args: T_ParamSpec.args, **kwargs: T_ParamSpec.kwargs) -> T_Retval:
        try:
            asynclib_name = sniffio.current_async_library()
        except sniffio.AsyncLibraryNotFoundError:
            pass
        else:
            if asynclib_name == "asyncio":
                try:
                    loop = get_running_loop()
                except RuntimeError:
                    pass
                else:
                    coro = func(*args, **kwargs)
                    try:
                        return loop.run_until_complete(coro)
                    except RuntimeError as e:
                        if "This event loop is already running" in str(e):
                            return run_async(ensure_afunc(coro))
                        else:
                            raise e
        return run_async(functools.partial(func, **kwargs), *args)

    return runner


def run_until_complete(
    async_func: Awaitable[T_Retval] | Callable[[], Awaitable[T_Retval]],
) -> T_Retval:
    """Run async function or coroutine in runing loop or worker thread"""
    return async_to_sync(ensure_afunc(async_func))()
