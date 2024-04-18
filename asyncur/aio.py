import sys
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable, Coroutine, Sequence, TypeVar

if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack
else:
    from exceptiongroup import ExceptionGroup  # pragma: no cover
    from typing_extensions import TypeVarTuple, Unpack  # pragma: no cover

import anyio

T_Retval = TypeVar("T_Retval")
PosArgsT = TypeVarTuple("PosArgsT")


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
    if not callable(func):

        async def do_await() -> T_Retval:
            return await func

        return anyio.run(do_await, backend=backend, backend_options=backend_options)
    return anyio.run(func, *args, backend=backend, backend_options=backend_options)


async def bulk_gather(
    coros: Sequence[Coroutine], limit=0, wait_last=False, raises=True
) -> tuple:
    """Similar like asyncio.gather, if bulk is not zero, running tasks will limit to {bulk} every moment.

    :param coros: Coroutines
    :param limit: running tasks limit number, set 0 to be unlimit
    :param wait_last: if True, wait last bulk tasks to complete then start new task group, else use anyio.CapacityLimiter to limit task number
    :param raises: if True, raise Exception when coroutine failed, else return None
    """
    total = len(coros)
    results = [None] * total

    async def runner(coro, i) -> None:
        results[i] = await coro

    async def limited_runner(coro, i, limiter) -> None:
        async with limiter:
            results[i] = await coro

    try:
        if limit:
            if wait_last:
                for start in range(0, total, limit):
                    async with anyio.create_task_group() as tg:
                        for index, coro in enumerate(coros[start : start + limit]):
                            tg.start_soon(runner, coro, start + index)
            else:
                limiter = anyio.CapacityLimiter(limit)
                async with anyio.create_task_group() as tg:
                    for i, coro in enumerate(coros):
                        tg.start_soon(limited_runner, coro, i, limiter)
        else:
            async with anyio.create_task_group() as tg:
                for i, coro in enumerate(coros):
                    tg.start_soon(runner, coro, i)
    except ExceptionGroup as e:
        if raises:
            raise e.exceptions[0]

    return tuple(results)


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


async def wait_for(coro: Coroutine, timeout: int | float) -> Any:
    """Similar like asyncio.wait_for"""
    with anyio.fail_after(timeout):
        return await coro
