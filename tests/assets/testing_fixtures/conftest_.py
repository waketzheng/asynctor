from main import app

from asynctor.testing import anyio_backend_fixture, async_client_fixture, chdir_tmp_fixture

anyio_backend = anyio_backend_fixture()
client = async_client_fixture(app)
tmp_work_dir = chdir_tmp_fixture()
