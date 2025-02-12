from __future__ import annotations

import concurrent.futures
import functools
import sys
from collections.abc import Callable
from contextlib import AbstractContextManager
from functools import cached_property
from threading import Thread
from typing import Annotated, Any, TypeVar

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import ParamSpec, Self
else:  # pragma: no cover
    from typing_extensions import ParamSpec, Self

T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")
FuncResults = Annotated[list, "The return value of each funtion or the exception that it raises"]


class StoredThread(Thread):
    def run(self):
        """Use a new attribute `_result` to stored target result or exception."""
        try:
            self._result = self._target(*self._args, **self._kwargs)  # type:ignore[attr-defined]
        except Exception as e:
            self._result = e


class ThreadGroup(AbstractContextManager):
    """
    Make it easy to wait for threads to complete, and better support for autocompletion.

    Use it like this:

    ```Python
    def do_work(arg1, arg2, kwarg1="", kwarg2="") -> str:
        # Do work

    with ThreadGroup() as tg:
        for _ in range(10):
            tg.soonify(do_work)("spam", "ham", kwarg1="a", kwarg2="b")

    print(f'All {len(tg.threads)} threads completed.')
    ```

    ## Arguments

    `max_workers`: if != 0, use `concurrent.futures.ThreadPoolExecutor(max_workers)`
    `timeout`: floating point number that specifying a timeout for the operation in seconds.
    """

    def __init__(self, max_workers: int | None = 0, timeout: float | None = None):
        self._threads: list[StoredThread] = []
        self._results: list[Any] = []
        self._timeout = timeout
        self._max_workers = max_workers
        self._executor: concurrent.futures.ThreadPoolExecutor | None = None
        self._future_idx: dict[concurrent.futures.Future, int] = {}

    @property
    def results(self) -> FuncResults:
        return self._results

    @cached_property
    def use_pool(self) -> bool:
        """Whether use ThreadPoolExecutor"""
        return self._max_workers != 0

    def __enter__(self) -> Self:
        if self.use_pool:
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self._max_workers
            ).__enter__()
        return self

    def soonify(self, func: Callable[T_ParamSpec, Any]) -> Callable[T_ParamSpec, None]:
        """
        Create and start a Thread instance then add it to this group.

        Use it like this:

        ```Python
        with ThreadGroup() as tg:
            def do_work(arg1, arg2, kwarg1="", kwarg2="") -> str:
                # Do work

            tg.soonify(do_work)("spam", "ham", kwarg1="a", kwarg2="b")

        ```
        """

        @functools.wraps(func)
        def runner(*args: T_ParamSpec.args, **kwargs: T_ParamSpec.kwargs) -> None:
            if self._executor is not None:
                fut = self._executor.submit(func, *args, **kwargs)
                self._future_idx[fut] = len(self._future_idx)
            else:
                t = StoredThread(target=func, args=args, kwargs=kwargs)
                t.start()
                self._threads.append(t)

        return runner

    def __exit__(self, *args, **kwargs):
        if fs := self._future_idx:
            self._results = [None] * len(fs)
            for future in concurrent.futures.as_completed(fs, timeout=self._timeout):
                idx = fs[future]
                try:
                    res = future.result()
                except Exception as exc:
                    res = exc
                self._results[idx] = res
        else:
            for t in self._threads:
                t.join(timeout=self._timeout)
            for t in self._threads:
                if t.is_alive():
                    fn, gs, kw = t._target, t._args, t._kwargs  # type:ignore[attr-defined]
                    if len(msg := f"{fn}(*{gs!r}, **{kw!r})") > 50:
                        msg = msg[:47] + "..."
                    res = TimeoutError(msg)
                else:
                    res = t._result
                self._results.append(res)


def _test() -> None:  # pragma: no cover
    import time

    def saying(msg="haha", loop=5, ident=0) -> float:
        print(msg)
        total = 0
        for i in range(loop):
            print(f"Sleeping {ident}: {i}/10 seconds")
            time.sleep(i / 10)
            total += i
        return round(total / 10, 1)

    with ThreadGroup() as tg:
        for i in range(10):
            tg.soonify(saying)(f"t{i + 1}", ident=i, loop=((i + 1) * 2 % 5 + 1))
    print(tg.results)
    print("Done.")


if __name__ == "__main__":
    _test()
