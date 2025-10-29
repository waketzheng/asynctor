from asynctor.testing import anyio_backend_fixture, chdir_tmp_fixture

anyio_backend = anyio_backend_fixture()
tmp_work_dir = chdir_tmp_fixture()
