from pathlib import Path

import pytest

from asynctor.testing import AsyncClient


@pytest.mark.anyio
async def test_index(client: AsyncClient):
    response = await client.get("/")
    assert response.json() == {"a": 1, "lifespan": False}


def test_current_dir_changed(tmp_workdir):
    pwd = Path.cwd()
    assert pwd == tmp_workdir
    root_dir = Path(__file__).parent
    assert pwd != root_dir
    assert not root_dir.is_relative_to(pwd)
