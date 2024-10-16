import importlib.metadata as importlib_metadata

from .aio import bulk_gather, gather, map_group, run, run_async, start_tasks, wait_for
from .client import AsyncRedis
from .timing import timeit
from .utils import AsyncTestClient, AttrDict, cache_attr

__version__ = importlib_metadata.version(__name__)
__all__ = (
    "__version__",
    "AsyncRedis",
    "AsyncTestClient",
    "AttrDict",
    "bulk_gather",
    "cache_attr",
    "gather",
    "map_group",
    "run",
    "run_async",
    "start_tasks",
    "timeit",
    "wait_for",
)
