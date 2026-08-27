import asyncio
import functools
from collections.abc import Generator
from datetime import datetime
from typing import Any

from asynctor import Timer, run_async


async def current_time(now: datetime | None = None) -> datetime:
    if now is None:
        now = Timer.beijing_now()
    await asyncio.sleep(0.1)
    return now


def sync_func() -> None:
    print(run_async(current_time))


class Clock:
    def __await__(self) -> Generator[Any, None, None]:
        async def _self() -> None:
            sync_func()

        return _self().__await__()


async def main() -> None:
    sync_func()
    now = run_async(current_time)
    later = run_async(current_time())
    assert later > now
    assert now == run_async(current_time, now)
    assert now == run_async(current_time(now))
    assert now == run_async(functools.partial(current_time, now=now))
    run_async(Clock())


if __name__ == "__main__":
    run_async(main)
