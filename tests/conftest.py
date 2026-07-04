import contextlib

with contextlib.suppress(RuntimeError):
    from asynctor.testing import anyio_backend_fixture, tmp_workdir_fixture

    anyio_backend = anyio_backend_fixture()
    tmp_workdir = tmp_workdir_fixture()
