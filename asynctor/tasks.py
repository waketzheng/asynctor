from __future__ import annotations

import functools
import sys
from contextlib import AbstractContextManager
from threading import Thread
from typing import Any, Callable, TypeVar

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:  # pragma: no cover
    from typing_extensions import ParamSpec

T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")


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

    `timeout`: floating point number that specifying a timeout for the operation in seconds.
    """

    def __init__(self, timeout: float | None = None):
        self.threads: list[StoredThread] = []
        self.results: list[Any] = []
        self.timeout = timeout

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
        def runner(*args: T_ParamSpec.args, **kwargs: T_ParamSpec.kwargs):
            t = StoredThread(target=func, args=args, kwargs=kwargs)
            t.start()
            self.threads.append(t)

        return runner

    def __exit__(self, *args, **kw):
        for t in self.threads:
            t.join(timeout=self.timeout)
        self.results = [t._result for t in self.threads]


def _test() -> None:  # pragma: no cover
    import random
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
            tg.soonify(saying)(f"t{i+1}", ident=i, loop=random.randint(1, 5))
    print(tg.results)
    print("haha")


if __name__ == "__main__":
    _test()
