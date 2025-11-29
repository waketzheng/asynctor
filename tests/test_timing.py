from __future__ import annotations

import time
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timedelta
from io import StringIO

import anyio
import pytest

from asynctor.timing import Timer, ZoneInfo, timeit


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
    async def test_start_capture(self):
        # Manual capture
        clock = Timer("testing start capture", decimal_places=2, verbose=False)
        assert repr(clock) == "Timer('testing start capture', 2, False)"
        start = time.time()
        assert clock._start <= start
        time.sleep(0.5)
        clock.start()
        assert clock._start > start
        with capture_stdout() as stream:
            await raw_sleep(0.23)
            clock.capture()
        assert not stream.getvalue()
        assert clock.cost == 0.23 or clock.cost == 0.24
        assert str(clock) == f"testing start capture Cost: {clock.cost} seconds"
        # with syntax
        with capture_stdout() as stream, Timer("Let it move:", verbose=False) as watch:
            time.sleep(0.3)
        assert not stream.getvalue()
        assert watch.cost == 0.3
        assert str(watch) == "Let it move: Cost: 0.3 seconds"
        # Explicit set verbose as True
        with capture_stdout() as stream, Timer("Let it move:", verbose=True):
            time.sleep(0.3)
        assert stream.getvalue().strip() == "Let it move: Cost: 0.3 seconds"
        # Initial with verbose False, but capture with verbose True
        pendulum = Timer("Initial verbose False but capture True", verbose=False)
        time.sleep(0.2)
        with capture_stdout() as stream:
            pendulum.capture(verbose=True)
        assert (
            stream.getvalue().strip() == "Initial verbose False but capture True Cost: 0.2 seconds"
        )
        # Initial with verbose True, capture will auto print cost message
        timepiece = Timer("I'm a teapot --")
        time.sleep(0.1)
        with capture_stdout() as stream:
            timepiece.capture()
        assert stream.getvalue().strip() == "I'm a teapot -- Cost: 0.1 seconds"

    @pytest.mark.anyio
    async def test_with(self):
        start = time.time()
        message = "Welcome to guangdong"
        with capture_stdout() as stream, Timer(message):
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
    async def test_get_cost(self):
        places = 3
        timer = Timer("Testing get cost", decimal_places=places, verbose=False)
        delay = 0.2
        await anyio.sleep(delay)
        assert round(timer.get_cost(), 1) == delay
        timer.capture()
        start = timer._end
        await anyio.sleep(delay)
        assert round(timer.get_cost(start), 1) == delay
        assert round(timer.get_cost(), 1) == delay * 2


@pytest.mark.anyio
async def test_with_timeit():
    start = time.time()
    message = "hello kitty"
    with capture_stdout() as stream, timeit(message):
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


def test_nows():
    utc_now = Timer.now()
    bj_now = Timer.beijing_now()
    assert str(utc_now).endswith("+00:00")
    assert str(bj_now).endswith("+08:00")
    assert "Asia/Shanghai" in repr(bj_now)
    tzinfo = bj_now.tzinfo
    assert tzinfo
    assert isinstance(tzinfo, ZoneInfo)
    assert "Asia/Shanghai" == tzinfo.key == tzinfo.zone
    utc_ts = utc_now.timestamp()
    bj_ts = bj_now.timestamp()
    assert bj_ts - utc_ts < 1
    assert round(utc_ts) == round(bj_ts)
    assert utc_ts == Timer.to_beijing(utc_now).timestamp()
    assert str(Timer.to_beijing(utc_now)).endswith("+08:00")
    fmt = "%Y-%m-%d %H:%M:%S"
    assert (
        datetime.strptime(str(Timer.to_beijing(utc_now)).split(".")[0], fmt)
        - datetime.strptime(str(utc_now).split(".")[0], fmt)
    ) == timedelta(hours=8)


def test_export():
    from asynctor import Timer as _Timer
    from asynctor import timeit as _timeit

    assert _Timer is Timer
    assert _timeit is timeit
