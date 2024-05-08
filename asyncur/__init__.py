import importlib.metadata
from pathlib import Path

from .aio import gather, run, run_async, start_tasks, wait_for
from .client import AsyncRedis
from .timing import timeit
from .utils import AttrDict

__version__ = importlib.metadata.version(Path(__file__).parent.name)
__all__ = (
    "__version__",
    "AsyncRedis",
    "AttrDict",
    "run",
    "run_async",
    "gather",
    "start_tasks",
    "timeit",
    "wait_for",
)
