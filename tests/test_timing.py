import time
from contextlib import contextmanager, redirect_stdout
from io import StringIO

import anyio
import pytest

from asynctor.timing import Timer, timeit


@contextmanager
def capture_stdout():
    """Redirect sys.stdout to a new StringIO

    Example::
    ```py
        with capture_stdout() as stream:
            GitTag(message="", dry=True).run()
        assert "git tag -a" in stream.getvalue()
    ```
    """
    stream = StringIO()
    with redirect_stdout(stream):
        yield stream


@timeit
async def sleep(seconds: float | int) -> None:
    return await raw_sleep(seconds)


@Timer
async def do_sleep(seconds):
    return await raw_sleep(seconds)


async def raw_sleep(seconds):
    await anyio.sleep(seconds)


@timeit
async def sleep1() -> int:
    return await raw_sleep1()


@Timer
async def do_sleep1() -> int:
    return await raw_sleep1()


async def raw_sleep1() -> int:
    await anyio.sleep(0.1)
    return 1


@timeit
def wait_for() -> str:
    return raw_wait_for()


@Timer
def do_wait_for() -> str:
    return raw_wait_for()


def raw_wait_for():
    time.sleep(0.12)
    return "I'm a teapot"


@pytest.mark.anyio
async def test_timeit():
    start = time.time()
    s = 0.2
    with capture_stdout() as stream:
        r = await sleep(s)
    end = time.time()
    assert round(end - start, 1) == s
    assert r is None
    stdout = stream.getvalue()
    assert str(s) in stdout and sleep.__name__ in stdout
    start = time.time()
    with capture_stdout() as stream1:
        r1 = await sleep1()
    end = time.time()
    assert round(end - start, 1) == 0.1
    assert r1 == 1
    stdout1 = stream1.getvalue()
    assert "0.1" in stdout1 and sleep1.__name__ in stdout1
    start = time.time()
    with capture_stdout() as stream2:
        r2 = wait_for()
    end = time.time()
    assert round(end - start, 1) == 0.1
    assert r2 == "I'm a teapot"
    stdout2 = stream2.getvalue()
    assert "0.1" in stdout2 and wait_for.__name__ in stdout2
    assert "0.12" not in stdout2


class TestTimer:
    @pytest.mark.anyio
    async def test_decorator(self):
        start = time.time()
        s = 0.2
        with capture_stdout() as stream:
            r = await do_sleep(s)
        end = time.time()
        assert round(end - start, 1) == s
        assert r is None
        stdout = stream.getvalue()
        assert str(s) in stdout and do_sleep.__name__ in stdout
        start = time.time()
        with capture_stdout() as stream1:
            r1 = await do_sleep1()
        end = time.time()
        assert round(end - start, 1) == 0.1
        assert r1 == 1
        stdout1 = stream1.getvalue()
        assert "0.1" in stdout1 and do_sleep1.__name__ in stdout1
        start = time.time()
        with capture_stdout() as stream2:
            r2 = do_wait_for()
        end = time.time()
        assert round(end - start, 1) == 0.1
        assert r2 == "I'm a teapot"
        stdout2 = stream2.getvalue()
        assert "0.1" in stdout2 and do_wait_for.__name__ in stdout2
        assert "0.12" not in stdout2

    @pytest.mark.anyio
    async def test_with(self):
        start = time.time()
        message = "Welcome to guangdong"
        with capture_stdout() as stream:
            with Timer(message):
                await raw_sleep1()
                raw_wait_for()
                await raw_sleep(0.21)
        end = time.time()
        assert round(end - start, 1) == (0.1 + 0.1 + 0.2)
        stdout = stream.getvalue()
        assert "0.4" in stdout
        assert raw_sleep.__name__ not in stdout
        assert raw_wait_for.__name__ not in stdout
        assert raw_sleep1.__name__ not in stdout
        assert message in stdout

    def test_invalid_use_case(self):
        assert Timer("")() is None


@pytest.mark.anyio
async def test_with_timeit():
    start = time.time()
    message = "hello kitty"
    with capture_stdout() as stream:
        with timeit(message):
            await raw_sleep1()
            raw_wait_for()
            await raw_sleep(0.21)
    end = time.time()
    assert round(end - start, 1) == (0.1 + 0.1 + 0.2)
    stdout = stream.getvalue()
    assert "0.4" in stdout
    assert raw_sleep.__name__ not in stdout
    assert raw_wait_for.__name__ not in stdout
    assert raw_sleep1.__name__ not in stdout
    assert message in stdout
