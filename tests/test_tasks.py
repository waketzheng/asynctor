import random
import time

from asynctor.tasks import ThreadGroup


def sleep(seconds=0.1):
    time.sleep(seconds)
    return seconds


def test_thread_group():
    total = 10
    start = time.time()
    with ThreadGroup() as tg:
        for _ in range(total):
            tg.soonify(sleep)()
    end = time.time()
    assert round(end - start, 1) == 0.1
    assert tg.results == [0.1] * total
    start = time.time()
    with ThreadGroup() as tg:
        for _ in range(total):
            tg.soonify(sleep)(0.2)
    end = time.time()
    assert round(end - start, 1) == 0.2
    assert tg.results == [0.2] * total
    start = time.time()
    choices = [0.1, 0.2, 0.3]
    seconds = [random.choice(choices) for _ in range(total)]
    with ThreadGroup() as tg:
        for t in seconds:
            tg.soonify(sleep)(seconds=t)
    end = time.time()
    assert round(end - start, 1) == max(seconds)
    assert len(tg.results) == total
    assert all(i in choices for i in tg.results)


def test_thread_group_timeout():
    def foo():
        return 1

    start = time.time()
    with ThreadGroup(timeout=0.1) as tg:
        tg.soonify(sleep)(seconds=0.2)
        tg.soonify(foo)()
    end = time.time()
    assert round(end - start, 1) == 0.1
    assert isinstance(tg.results[0], TimeoutError)
    assert tg.results[1] == 1
    assert len(tg.results) == 2


def test_thread_group_exception():
    def raise_it(e: Exception):
        raise e

    with ThreadGroup() as tg:
        tg.soonify(raise_it)(ValueError("foo"))
        tg.soonify(raise_it)(TypeError("type"))

    assert len(tg.results) == 2
    assert isinstance(tg.results[0], ValueError)
    assert isinstance(tg.results[1], TypeError)
    assert str(tg.results[0]) == "foo"
    assert str(tg.results[1]) == "type"

    with ThreadGroup(max_workers=None) as tg:
        tg.soonify(raise_it)(ValueError("foo"))
        tg.soonify(raise_it)(TypeError("type"))

    assert len(tg.results) == 2
    assert isinstance(tg.results[0], ValueError)
    assert isinstance(tg.results[1], TypeError)
    assert str(tg.results[0]) == "foo"
    assert str(tg.results[1]) == "type"


def test_thread_group_with_pool():
    start = time.time()
    with ThreadGroup(max_workers=1) as tg:
        tg.soonify(sleep)(seconds=0.1)
        tg.soonify(sleep)(seconds=0.2)
    end = time.time()
    assert round(end - start, 1) == 0.3
    assert tg.results[0] == 0.1
    assert tg.results[1] == 0.2
