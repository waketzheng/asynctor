from collections.abc import Generator
from pathlib import Path

import pytest

from asynctor.compat import chdir


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def tmp_work_dir(tmp_path: Path) -> Generator[Path]:
    with chdir(tmp_path):
        yield tmp_path
