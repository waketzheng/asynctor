from __future__ import annotations

import asyncio
import functools
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import anyio
import pytest

from asynctor.aio import bulk_gather, gather, run, run_async, start_tasks, wait_for
from asynctor.exceptions import ParamsError
from asynctor.timing import Timer


def test_run_async():
    async def foo(sth: Any = ""):
        return sth

    assert run_async(foo) == ""
    assert run_async(foo()) == ""
    assert run_async(foo(1)) == 1
    assert run_async(foo(None)) is None
    assert run_async(foo(foo)) == foo
    assert run_async(functools.partial(foo, 2)) == 2


def test_run():
    async def foo(sth: Any = ""):
        return sth

    assert run(foo) == ""
    assert run(foo()) == ""
    assert run(foo(1)) == 1
    assert run(foo(None)) is None
    assert run(foo(foo)) == foo
    assert run(functools.partial(foo, 2)) == 2
    assert run(foo, 2) == 2
    assert run(foo, 2, backend="asyncio") == 2
    assert run(foo, 2, backend="asyncio", backend_options=None) == 2


@pytest.mark.anyio
async def test_wait_for():
    async def do_sth(seconds=0.2):
        await anyio.sleep(seconds)
        return seconds

    assert (await wait_for(do_sth(), 1)) == 0.2
    with pytest.raises(TimeoutError):
        await wait_for(do_sth(), 0.1)


class MockServer:
    limit = 50
    count = 0
    OK = 200
    ERROR = 400

    @classmethod
    async def response(cls) -> int:
        cls.count += 1
        await anyio.sleep(0.1)
        status_code = cls.OK
        if cls.count > cls.limit:
            status_code = cls.ERROR
        cls.count -= 1
        return status_code


class TestGather:
    @pytest.mark.anyio
    async def test_gather(self):
        assert (await gather()) == ()

        async def a():
            return 1

        async def b():
            return "2"

        async def c():
            pass

        assert (await gather(a(), b(), c())) == (1, "2", None)

    @staticmethod
    async def raise_error_later(seconds, err_type):
        await anyio.sleep(seconds)
        raise err_type(f"{seconds = }")

    @staticmethod
    def is_the_same_error(e1, e2):
        return type(e1) is type(e2) and str(e1) == str(e2)

    def create_coros_for_raise(self):
        coro1 = self.raise_error_later(0.2, ValueError)
        coro2 = self.raise_error_later(0.1, AttributeError)
        coro3 = self.raise_error_later(0.11, OSError)
        return coro1, coro2, coro3

    @pytest.mark.anyio
    async def test_gather_raise(self):
        err_asyncio = err_anyio = None
        try:
            await asyncio.gather(*self.create_coros_for_raise())
        except Exception as e:
            err_asyncio = e
        try:
            await gather(*self.create_coros_for_raise())
        except Exception as e:
            err_anyio = e
        assert self.is_the_same_error(err_asyncio, err_anyio)

    @pytest.mark.anyio
    async def test_gather_without_raise(self):
        results = await bulk_gather(self.create_coros_for_raise(), raises=False)
        assert results == (None, None, None)

    @pytest.mark.anyio
    async def test_bulk(self):
        total = 200
        with Timer("Use sema:"):
            tasks = [MockServer.response() for _ in range(total)]
            results = await bulk_gather(tasks, MockServer.limit)
            assert sum(i == MockServer.OK for i in results) == total
        with Timer("Without sema:"):
            tasks = [MockServer.response() for _ in range(total)]
            results = await bulk_gather(tasks, MockServer.limit, wait_last=True)
            assert all(i == MockServer.OK for i in results)
        with Timer("All start:"):
            tasks = [MockServer.response() for _ in range(total)]
            results = await gather(*tasks)
            assert any(i == MockServer.ERROR for i in results)

    @pytest.mark.anyio
    async def test_bulk_batch_size(self):
        total = 200
        with Timer("Use sema:"):
            tasks = [MockServer.response() for _ in range(total)]
            results = await bulk_gather(tasks, batch_size=MockServer.limit)
            assert sum(i == MockServer.OK for i in results) == total
        with Timer("Without sema:"):
            tasks = [MockServer.response() for _ in range(total)]
            results = await bulk_gather(tasks, batch_size=MockServer.limit, wait_last=True)
            assert all(i == MockServer.OK for i in results)

    @pytest.mark.anyio
    async def test_bulk_batch_size_generator(self):
        total = 200
        with Timer("Use sema(generator):"):
            tasks = (MockServer.response() for _ in range(total))
            results = await bulk_gather(tasks, batch_size=MockServer.limit)
            assert sum(i == MockServer.OK for i in results) == total
        with Timer("Without sema(generator):"):
            tasks = (MockServer.response() for _ in range(total))
            results = await bulk_gather(tasks, batch_size=MockServer.limit, wait_last=True)
            assert all(i == MockServer.OK for i in results)

    @pytest.mark.anyio
    async def test_bulk_limit(self):
        total = 200
        with Timer("Use sema:"):
            tasks = [MockServer.response() for _ in range(total)]
            results = await bulk_gather(tasks, limit=MockServer.limit)
            assert sum(i == MockServer.OK for i in results) == total
        with Timer("Without sema:"):
            tasks = [MockServer.response() for _ in range(total)]
            results = await bulk_gather(tasks, limit=MockServer.limit, wait_last=True)
            assert all(i == MockServer.OK for i in results)

    @pytest.mark.anyio
    async def test_bulk_limit_generator(self):
        total = 200
        with Timer("Use sema(generator):"):
            tasks = (MockServer.response() for _ in range(total))
            results = await bulk_gather(tasks, limit=MockServer.limit)
            assert sum(i == MockServer.OK for i in results) == total
        with Timer("Without sema(generator):"):
            tasks = (MockServer.response() for _ in range(total))
            results = await bulk_gather(tasks, limit=MockServer.limit, wait_last=True)
            assert all(i == MockServer.OK for i in results)

    @pytest.mark.anyio
    async def test_bulk_conflict_or_warning(self):
        tasks = [MockServer.response() for _ in range(200)]
        with pytest.raises(ParamsError):
            await bulk_gather(tasks, batch_size=MockServer.limit + 1, limit=MockServer.limit)
        with pytest.deprecated_call():
            await bulk_gather(tasks, batch_size=MockServer.limit, limit=MockServer.limit)

    @pytest.mark.anyio
    async def test_bulk_gather_generator(self):
        async def a():
            return 1

        lazy_tasks = (a() for _ in range(3))
        assert (await bulk_gather(lazy_tasks)) == (1, 1, 1)


class TestStartTasks:
    root = anyio.Path(__file__).parent
    names = ("tmp.txt", "tmp2.txt", "tmp3.txt")

    async def remove_files(self):
        for name in self.names:
            if await (p := self.root / name).exists():
                await p.unlink()

    async def startup(self):
        await self.root.joinpath(self.names[0]).touch()
        await anyio.sleep(1)
        await self.root.joinpath(self.names[1]).touch()

    async def running(self):
        while True:
            now = datetime.now()
            await self.root.joinpath(self.names[2]).write_text(str(now))
            await anyio.sleep(0.5)

    @pytest.mark.anyio
    async def test_start_tasks(self):
        await self.remove_files()
        root, names = self.root, self.names

        @asynccontextmanager
        async def lifespan(app):
            now = datetime.now()
            async with start_tasks(self.startup, self.running):
                await anyio.sleep(0.1)
                assert await root.joinpath(names[0]).exists()
                assert not (await root.joinpath(names[1]).exists())
                assert await root.joinpath(names[2]).exists()
                await anyio.sleep(1)
                assert await root.joinpath(names[0]).exists()
                assert await root.joinpath(names[1]).exists()
                assert (await root.joinpath(names[2]).read_text()) > str(now)
                yield
            now = datetime.now()
            assert (await root.joinpath(names[2]).read_text()) <= str(now)
            await self.remove_files()

        async with lifespan(None):
            for name in names:
                assert await root.joinpath(name).exists()

        for name in names:
            assert not await root.joinpath(name).exists()
