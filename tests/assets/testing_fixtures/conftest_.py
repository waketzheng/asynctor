from main import app  # ty:ignore[unresolved-import]

from asynctor.testing import anyio_backend_fixture, async_client_fixture, tmp_workdir_fixture

anyio_backend = anyio_backend_fixture()
client = async_client_fixture(app)
tmp_work_dir = tmp_workdir_fixture()
