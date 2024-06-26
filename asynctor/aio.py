import itertools
import sys
import warnings
from contextlib import asynccontextmanager
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Generator,
    Iterable,
    Sequence,
    TypeVar,
)

import anyio

from .exceptions import ParamsError

if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from exceptiongroup import ExceptionGroup  # pragma: no cover
    from typing_extensions import TypeVarTuple, Unpack  # pragma: no cover


T_Retval = TypeVar("T_Retval")
PosArgsT = TypeVarTuple("PosArgsT")
AsyncFunc = Callable[..., Coroutine]


def ensure_afunc(
    coro: Coroutine[None, None, T_Retval] | Callable[..., Awaitable[T_Retval]],
) -> Callable[..., Awaitable[T_Retval]]:
    """Wrap coroutine to be async function"""
    if callable(coro):
        return coro

    async def do_await():
        return await coro

    return do_await


def run_async(
    coro: Coroutine[None, None, T_Retval] | Callable[..., Awaitable[T_Retval]],
) -> T_Retval:
    """Compare with anyio.run and asyncio.run

    Usage::
        >>> async def afunc(n=1):
        ...     return n
        ...
        >>> run_async(afunc)  # get the same result as: await afunc()
        1
        >>> run_async(afunc(2))  # get the same result as: await afunc(2)
        2
    """
    return anyio.run(ensure_afunc(coro))


def run(
    func: (
        Coroutine[None, None, T_Retval]
        | Callable[[Unpack[PosArgsT]], Awaitable[T_Retval]]
    ),
    *args: Unpack[PosArgsT],
    backend: str = "asyncio",
    backend_options: dict[str, Any] | None = None,
) -> T_Retval:
    """Combine `asyncio.run` and `anyio.run`

    :param func: async function or coroutine.
    :param *args: arguments that will pass to `func` if it's a function.
    :param backend: should be 'asyncio' or 'trio'.
    :param backend_options: will pass to `anyio.run`.

    Usage::

    .. code-block:: python3

        async def foo(a, b, *, c=3):
            return a, b, c

        from functools import partial
        assert run(partial(foo, c=0), 1, 2) == run(foo(1, 2, c=0))

    """
    if not callable(func):

        async def do_await() -> T_Retval:
            return await func

        return anyio.run(do_await, backend=backend, backend_options=backend_options)
    return anyio.run(func, *args, backend=backend, backend_options=backend_options)


async def bulk_gather(
    coros: Sequence[Coroutine] | Generator[Coroutine, None, None],
    batch_size=0,
    wait_last=False,
    raises=True,
    *,
    limit: int | None = None,
) -> tuple:
    """Similar like `asyncio.gather`, if batch_size is not zero, running tasks will CapacityLimiter({batch_size}).

    :param coros: Coroutines
    :param batch_size: running tasks limit number, set 0 to be unlimit.
    :param wait_last: if True, wait last bulk tasks to complete then start new task group,
        else use anyio.CapacityLimiter to limit task number.
    :param raises: if True, raise Exception when coroutine failed, else return None.
    :param limit: (deprecated) only leave it here to compare with old version.
    """
    try:
        total = len(coros)  # type:ignore[arg-type]
    except TypeError:  # if coros is generator
        total = 0
    else:
        if total == 0:
            return ()
    results = [None] * total

    async def runner(_i: int, _coro: Coroutine) -> None:
        results[_i] = await _coro

    async def limited_runner(_i, _coro, _limiter) -> None:
        async with _limiter:
            results[_i] = await _coro

    try:
        if limit is not None:
            if batch_size:
                if batch_size != limit:
                    raise ParamsError(f"Conflict value with {limit=} & {batch_size=}")
                else:
                    warnings.warn(
                        "`limit` is deprecated, it's replaced by `batch_size`, feel free to keep only one.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
            else:
                batch_size = limit
        if batch_size:
            if wait_last:
                if total == 0:
                    todos: list[tuple[int, Coroutine]] = []
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
                        args_items = (
                            (start + i, coro) for i, coro in enumerate(coros_slice)
                        )
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
            raise e.exceptions[0]

    return tuple(results)


async def map_group(
    func: AsyncFunc, todos: Iterable, results: list | None = None
) -> None:
    async with anyio.create_task_group() as tg:
        for args in todos:
            if results is not None:
                results.append(None)
            tg.start_soon(func, *args)


async def gather(*coros: Coroutine) -> tuple:
    """Similar like asyncio.gather"""
    return await bulk_gather(coros)


@asynccontextmanager
async def start_tasks(coro: Coroutine | Callable, *more: Coroutine | Callable):
    """Make it easy to convert asyncio.create_task

    Usage:

    .. code-block:: python3

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


async def wait_for(
    coro: Coroutine[None, None, T_Retval], timeout: int | float
) -> T_Retval:
    """Similar like asyncio.wait_for"""
    with anyio.fail_after(timeout):
        return await coro
