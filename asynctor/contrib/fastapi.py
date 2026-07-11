from __future__ import annotations

import copy
import functools
import logging
import os
import platform
import re
import sys
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, TypeAlias

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.routing import _merge_lifespan_context

from ..client import AsyncRedis
from ..exceptions import UnsupportedError
from ..timing import Timer
from ..utils import Shell, load_bool


def register_aioredis(
    app: FastAPI,
    check_connection: bool = True,
    **kwargs: Annotated[Any, "Kwargs that will pass to `redis.asyncio.Redis.__init__`"],
) -> None:
    """Register an async Redis client on a FastAPI application.

    The client is created during FastAPI lifespan startup, stored on
    ``app.state.redis``, and closed when the lifespan exits. Any existing
    lifespan context on the application is preserved.

    :param app: the FastAPI application instance.
    :param check_connection: if True, ping Redis while entering the lifespan.
    :param kwargs: Redis connection options such as ``host`` and ``port``.

    Usage::

        from fastapi import FastAPI
        from asynctor.contrib.fastapi import register_aioredis

        app = FastAPI()
        register_aioredis(app, host="localhost")
    """

    @asynccontextmanager
    async def redis_lifespan(app_instance: FastAPI) -> AsyncGenerator[None]:
        async with AsyncRedis(app_instance, check_connection=check_connection, **kwargs):
            yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _merge_lifespan_context(redis_lifespan, original_lifespan)


async def get_redis_client(request: Request) -> AsyncRedis:
    """Return the registered Redis client for the current request.

    The application must have a Redis client mounted on ``app.state.redis``,
    typically by calling ``register_aioredis(app)``.

    :param request: the incoming FastAPI request.
    :return: the ``AsyncRedis`` instance stored on the FastAPI application.
    """
    return AsyncRedis(request)


AioRedisDep = Annotated[AsyncRedis, Depends(get_redis_client)]
AioRedisDep.__doc__ = """Get the registered Redis client from the application.

Example::

    from asynctor.contrib.fastapi import AioRedisDep, register_aioredis
    from fastapi import FastAPI

    app = FastAPI()
    register_aioredis(app)

    @app.get('/')
    async def get_redis_keys(redis: AioRedisDep) -> list[str]:
        keys = await redis.keys()
        return keys

"""
AioRedis = AioRedisDep  # For compatible


def get_client_ip(request: Request) -> str:
    """Resolve the original client IP address for a request.

    Proxy headers are checked before falling back to the socket peer address.
    The lookup order is ``X-Forwarded-For``, ``X-Real-IP``, ``Forwarded``, and
    finally ``request.client.host``.

    :param request: the incoming FastAPI request.
    :return: the resolved client IP address, or an empty string if unavailable.
    """
    headers = request.headers
    # X-Forwarded-For may include many IP addresses; the first one is the origin IP.
    if (x_forwarded_for := headers.get("x-forwarded-for") or headers.get("x_forwarded_for")) and (
        client_ip := x_forwarded_for.split(",", 1)[0].strip()
    ):
        return client_ip
    if (x_real_ip := headers.get("x-real-ip") or headers.get("x_real_ip")) and (
        client_ip := x_real_ip.strip()
    ):
        return client_ip
    if forwarded := headers.get("forwarded"):
        # Forwarded: for=192.0.2.60;proto=http;by=203.0.113.43
        for forwarded_item in forwarded.split(","):
            for part in forwarded_item.split(";"):
                key, _, value = part.strip().partition("=")
                if key.lower() == "for" and (client_ip := value.strip().strip('"')):
                    return client_ip
    if request.client is None:  # pragma: no cover
        # request.client is not None if server started by uvicorn
        # put it here to improve type hints
        return ""
    return request.client.host


async def get_client_host(request: Request) -> str:
    """FastAPI dependency that returns the request client IP address.

    This async wrapper avoids FastAPI running the dependency in a thread pool
    while reusing ``get_client_ip`` for the actual header parsing.

    :param request: the incoming FastAPI request.
    :return: the resolved client IP address.
    """
    # If the function is non-async and you use it as a dependency, it will run in a thread.
    # https://github.com/kludex/fastapi-tips?tab=readme-ov-file#9-your-dependencies-may-be-running-on-threads
    return get_client_ip(request)


ClientIpDep = Annotated[str, Depends(get_client_host)]
ClientIpDep.__doc__ = """Get the real IP address of the request client.

Usage::

    >>> @app.get('/')
    >>> def index(client_ip: ClientIpDep):
    ...     assert isinstance(client_ip, str)
"""

ACCESS_LOG_FMT = "%(asctime)s - %(levelname)s - %(message)s"


def config_access_log(fmt: FastAPI | str = ACCESS_LOG_FMT, log: str = "uvicorn.access") -> None:
    """Configure the uvicorn access logger format.

    A ``logging.StreamHandler`` with the provided formatter is added to the
    target logger. Passing a ``FastAPI`` instance as ``fmt`` is accepted for
    backward compatibility with ``config_access_log(app)``.

    :param fmt: the logging format string to use.
    :param log: the logger name to configure.

    Usage::

        >>> from asynctor.contrib.fastapi import config_access_log
        >>> app = FastAPI()
        >>> config_access_log()
    """
    if isinstance(fmt, FastAPI):  # Support `config_access_log(app)`
        fmt = ACCESS_LOG_FMT
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    logging.getLogger(log).addHandler(handler)


def config_access_log_to_show_time(log: str = "uvicorn.access") -> None:
    """Configure uvicorn access logs with the default asynctor format.

    :param log: the logger name to configure.

    Usage::

        >>> from asynctor.contrib.fastapi import config_access_log_to_show_time
        >>> app = FastAPI()
        >>> config_access_log_to_show_time()
    """
    config_access_log(log=log)


PreStartFunc: TypeAlias = Callable[
    [
        Annotated[str, "host"],
        Annotated[int | None, "port"],
        Annotated[bool, "reload"],
        Annotated[dict[str, str] | None, "docs_params"],
    ],
    Any,
]


class RunServer:
    """Implementation helpers used by ``runserver``."""

    @staticmethod
    def uvicorn_run(app: FastAPI, host: str, port: int | None, reload: bool, **kw) -> None:
        """Start uvicorn with the resolved application and network options.

        When reload is enabled, uvicorn receives ``"__main__:app"`` because
        reload mode requires an import string. Otherwise the FastAPI instance is
        passed directly.

        :param app: the FastAPI application instance to run.
        :param host: the host interface passed to uvicorn.
        :param port: the port passed to uvicorn; if None, uvicorn chooses its default.
        :param reload: whether to enable uvicorn reload mode.
        :param kw: additional keyword arguments passed to ``uvicorn.run``.
        """
        asgi = "__main__:app" if reload else app
        run = functools.partial(uvicorn.run, asgi, host=host, reload=reload, **kw)
        if port:
            run(port=port)
        else:
            run()

    @staticmethod
    def parse_host_port(
        addrport: str | int, verbose: bool, echo: Callable
    ) -> tuple[str | None, int | None]:
        """Parse a CLI address or port argument into host and port overrides.

        Accepted forms include ``9000``, ``":9000"``, ``"127.0.0.1:9000"``,
        and ``"0:9000"``. A returned value of None means the existing option
        should be kept.

        :param addrport: a port number, or a ``host:port`` value.
        :param verbose: whether to print a message for ignored values.
        :param echo: callback used to print verbose messages.
        :return: a ``(host, port)`` tuple containing parsed overrides.
        """
        host, port = None, None
        if isinstance(addrport, int) or addrport.isdigit():
            port = int(addrport)
        elif ":" in addrport:
            h, p = addrport.split(":", 1)
            if not h:
                host = "127.0.0.1"
            elif h != "0":
                host = h
            if p.isdigit():
                port = int(p)
        elif verbose:
            echo(f"Ignore argument {addrport = }")
        return host, port

    @staticmethod
    def load_prod_port(config_file: Path, verbose: bool, echo: Callable) -> int:
        """Load a production port from a gunicorn config file.

        The config module is imported from ``config_file``. ``PORT`` is used
        first; otherwise the final port segment of ``bind`` is used when it is
        numeric.

        :param config_file: path to a Python gunicorn config file.
        :param verbose: whether to print diagnostic messages.
        :param echo: callback used to print diagnostic messages.
        :return: the configured port, or 0 when no usable port is found.
        """
        import importlib.util

        spec = importlib.util.spec_from_file_location(config_file.stem, config_file)
        if spec is not None and spec.loader is not None:
            gunicorn_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gunicorn_config)
            if p := getattr(gunicorn_config, "PORT", 0):
                if verbose:
                    echo(f"Load `PORT = {p}` from {config_file}")
                return int(p)
            elif (p := getattr(gunicorn_config, "bind", "").split(":")[-1]).isdigit():
                if verbose:
                    echo(f"Load `bind = xxx:{p}` from {config_file}")
                return int(p)
            elif verbose:
                echo(f"{config_file} does not have 'PORT' attribute")
        elif verbose:
            echo(f"Failed to load module from {config_file}")
        return 0

    @staticmethod
    def echo_docs_url(
        app: FastAPI,
        host: str,
        port: int | None,
        docs_params: dict | None = None,
        echo: Callable | None = None,
    ) -> str:
        """Build, print, and return the FastAPI documentation URL.

        If ``host`` is ``"0.0.0.0"``, the displayed host is replaced by
        ``ASYNCTOR_HOST`` when set, or by the machine IP address otherwise.

        :param app: the FastAPI application whose ``docs_url`` is used.
        :param host: the configured server host.
        :param port: the configured server port; defaults to 8000 for display.
        :param docs_params: optional query parameters appended to the docs URL.
        :param echo: optional output callback; ``print`` is used when omitted.
        :return: the documentation URL that was printed.
        """
        if host == "0.0.0.0":  # nosec:B104
            if declared_host := os.getenv("ASYNCTOR_HOST"):
                host = declared_host
            else:
                from asynctor.utils import get_machine_ip

                host = get_machine_ip()
        url = f"http://{host}:{port or 8000}{app.docs_url}"
        if docs_params:
            url += "?" + "&".join(f"{k}={v}" for k, v in docs_params.items())
        tip = "You can view docs at:"
        if echo is None:
            print(f"{tip}\n{url}")
        else:
            echo(tip)
            try:
                echo(url, bold=True)
            except TypeError:
                echo(url)
        return url

    @staticmethod
    def load_port_from_env() -> int | None:
        """Load ``ASYNCTOR_PORT`` from the environment.

        :return: the integer port value, or None when unset or invalid.
        """
        if p := os.getenv("ASYNCTOR_PORT"):
            try:
                return int(p)
            except ValueError:
                ...
        return None

    @classmethod
    def run(
        cls,
        app: FastAPI,
        addrport: str | None,
        port: int | None,
        host: str,
        reload: bool,
        prod: bool,
        verbose: bool,
        echo: Callable,
        docs_params: dict[str, str] | None = None,
        pre_start: PreStartFunc | None = None,
        open_browser: bool | None = None,
        **kw,
    ) -> None:
        """Resolve command-line server options and start uvicorn.

        ``addrport`` takes precedence over ``host`` and ``port``. When
        ``prod`` is enabled and no ``addrport`` is provided, parent directories
        are scanned for ``deployment/gunicorn_config.py`` and the port is loaded
        from that file when possible.

        :param app: the FastAPI application instance to run.
        :param addrport: optional port number, or ``host:port`` value.
        :param port: explicit server port.
        :param host: server host interface.
        :param reload: whether to enable uvicorn reload mode.
        :param prod: whether to discover the port from a deployment config.
        :param verbose: whether to print diagnostic messages.
        :param echo: callback used to print messages.
        :param docs_params: optional query parameters appended to the docs URL.
        :param pre_start: optional callback invoked before uvicorn starts.
        :param open_browser: browser-opening option accepted by the public API.
        :param kw: additional keyword arguments passed to ``uvicorn.run``.
        """
        if addrport:
            h, p = cls.parse_host_port(addrport, verbose, echo)
            if h:
                host = h
            if p:
                port = p
        elif prod:
            deployment_dir = Path("deployment")
            for level in range(5):
                if deployment_dir.exists():
                    if (gc := deployment_dir / "gunicorn_config.py").exists():
                        if _port := cls.load_prod_port(gc, verbose, echo):
                            port = _port
                    elif verbose:
                        echo(f"{gc.name} not found in {deployment_dir}")
                    break
                parent = Path.cwd().parent if level == 0 else deployment_dir.parent.parent
                deployment_dir = parent / deployment_dir.name
            else:
                if verbose:
                    echo(f"Deployment dir: {deployment_dir.name!r} not found")
        cls.echo_and_run(app, host, port, reload, docs_params, pre_start, echo, **kw)

    @classmethod
    def echo_and_run(cls, app, host, port, reload, docs_params, pre_start, echo=None, **kw) -> None:
        """Print the docs URL, run startup hooks, optionally open it, then start uvicorn.

        If ``port`` is not supplied, ``ASYNCTOR_PORT`` is used when it contains
        a valid integer. The ``open_browser`` keyword or ``ASYNCTOR_BROWSER``
        controls whether the docs URL is opened before the server starts.

        :param app: the FastAPI application instance to run.
        :param host: server host interface.
        :param port: explicit server port.
        :param reload: whether to enable uvicorn reload mode.
        :param docs_params: optional query parameters appended to the docs URL.
        :param pre_start: optional callback invoked before uvicorn starts.
        :param echo: optional output callback.
        :param kw: additional keyword arguments passed to ``uvicorn.run``.
        """
        if not port:
            port = cls.load_port_from_env()
        url = cls.echo_docs_url(app, host, port, docs_params, echo)
        if pre_start is not None:
            try:
                pre_start(host=host, port=port, reload=reload, docs_params=docs_params)
            except TypeError:
                pre_start()
        if kw.pop("open_browser", False) or load_bool("ASYNCTOR_BROWSER"):
            command = "explorer" if platform.system() == "Windows" else "open"
            if host == "0.0.0.0" and (m := re.search(r"://(.*?)[:/]", url)):  # nosec:B104
                url = url.replace(m.group(1), "127.0.0.1")
            Shell([command, url]).run(verbose=True)
        cls.uvicorn_run(app, host, port, reload, **kw)


@functools.cache
def get_log_config(fmt: str) -> dict[str, Any]:
    """Return a cached uvicorn logging config with a custom access-log format.

    :param fmt: the access-log formatter string.
    :return: a copied uvicorn logging config dictionary.
    """
    from uvicorn.config import LOGGING_CONFIG

    log_config = copy.deepcopy(LOGGING_CONFIG)
    log_config["formatters"]["access"]["fmt"] = fmt
    return log_config


def runserver(
    app: FastAPI,
    addrport: str | int | None = None,
    port: int | None = None,
    host: str = "0.0.0.0",  # nosec:B104
    reload: bool = False,
    verbose: bool = False,
    docs_params: dict[str, str] | None = None,
    pre_start: PreStartFunc | None = None,
    open_browser: bool | None = None,
    log_access_time: bool = True,
    **kw,
) -> None:
    """Run a FastAPI application with asynctor's development server helper.

    With no command-line arguments, the application starts immediately. When
    command-line arguments are present, ``typer`` is used to expose options for
    ``addrport``, ``port``, ``host``, ``reload``, ``prod``, and ``verbose``.
    The Django-style ``--noreload`` flag is translated to ``--no-reload``.

    :param app: the FastAPI application instance to run.
    :param addrport: optional port number, or ``host:port`` value.
    :param port: explicit server port.
    :param host: server host interface.
    :param reload: whether to enable uvicorn reload mode.
    :param verbose: whether to print diagnostic messages.
    :param docs_params: optional query parameters appended to the docs URL.
    :param pre_start: optional callback invoked before uvicorn starts.
    :param open_browser: whether to open the docs URL before the server starts.
    :param log_access_time: whether to install the default access-log format.
    :param kw: additional keyword arguments passed to ``uvicorn.run``.
    :raises UnsupportedError: if ``log_access_time`` and ``log_config`` are both supplied.
    :raises ImportError: if command-line arguments are used without ``typer`` installed.

    Usage::

        from fastapi import FastAPI
        from asynctor.contrib.fastapi import runserver

        app = FastAPI()

        if __name__ == "__main__":
            runserver(app, reload=True)
    """
    kw.update(docs_params=docs_params, pre_start=pre_start, open_browser=open_browser)
    if log_access_time:
        if (log_config := kw.get("log_config")) is not None:
            raise UnsupportedError(f"Argument value conflict: {log_access_time=} vs {log_config=}")
        log_config = get_log_config(ACCESS_LOG_FMT)
        kw.update(log_config=log_config)
    if not (args := sys.argv[1:]):
        return RunServer.echo_and_run(app, host, port, reload, **kw)
    try:
        import typer
    except ImportError as e:
        raise type(e)(
            "You must install typer to support arguments, e.g.: pip install typer"
        ) from None

    def cli(
        addrport: Annotated[str | None, "Optional port number, or ipaddr:port"] = typer.Argument(
            default=addrport
        ),
        port: int | None = port,
        host: str = host,
        reload: bool = reload,
        prod: bool = False,
        verbose: bool = verbose,
    ) -> None:
        RunServer.run(app, addrport, port, host, reload, prod, verbose, echo=typer.secho, **kw)

    if (django_style_noreload := "--noreload") in args:
        sys.argv[sys.argv.index(django_style_noreload)] = "--no-reload"

    typer.run(cli)


def add_timing_middleware(app: FastAPI, header: str = "X-Process-Time") -> None:
    """Add middleware that writes request processing time to a response header.

    The measured duration is written as an integer number of milliseconds.

    :param app: the FastAPI application instance to update.
    :param header: response header name used for the elapsed time.

    Usage::

        from fastapi import FastAPI
        from asynctor.contrib.fastapi import add_timing_middleware

        app = FastAPI()
        add_timing_middleware(app)
    """

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        with Timer(request.url.path, decimal_places=3, verbose=False) as t:
            response = await call_next(request)
        response.headers[header] = f"{int(t.cost * 1000)} ms"
        return response
