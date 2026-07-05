from asynctor.testing import anyio_backend_fixture, async_client_fixture
from asynctor.utils import ExtendSyspath

with ExtendSyspath(__file__):
    from main import app  # ty:ignore[unresolved-import]

anyio_backend = anyio_backend_fixture()
client = async_client_fixture(app)
