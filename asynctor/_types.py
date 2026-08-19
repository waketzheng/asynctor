from __future__ import annotations

import asyncio
import os
import ssl
import sys
from collections.abc import Callable
from configparser import RawConfigParser
from typing import IO, TYPE_CHECKING, Any, Protocol, TypedDict

import click
from uvicorn.config import (
    INTERFACES,
    Config,
    HTTPProtocolType,
    InterfaceType,
    LifespanType,
    LoopFactoryType,
    WSProtocolType,
)

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import NotRequired
    else:
        from typing_extensions import NotRequired


# LEVEL_CHOICES = click.Choice(list(LOG_LEVELS.keys()))
# LIFESPAN_CHOICES = click.Choice(list(LIFESPAN.keys()))
INTERFACE_CHOICES = click.Choice(INTERFACES)


class UvicornKwargs(TypedDict, total=False):
    uds: NotRequired[str | None]
    fd: NotRequired[int | None]
    loop: NotRequired[LoopFactoryType | str]
    http: NotRequired[type[asyncio.Protocol] | HTTPProtocolType | str]
    ws: NotRequired[type[asyncio.Protocol] | WSProtocolType | str]
    ws_max_size: NotRequired[int]
    ws_max_queue: NotRequired[int]
    ws_ping_interval: NotRequired[float | None]
    ws_ping_timeout: NotRequired[float | None]
    ws_per_message_deflate: NotRequired[bool]
    lifespan: NotRequired[LifespanType]
    interface: NotRequired[InterfaceType]
    reload_dirs: NotRequired[list[str] | str | None]
    reload_includes: NotRequired[list[str] | str | None]
    reload_excludes: NotRequired[list[str] | str | None]
    reload_delay: NotRequired[float]
    workers: NotRequired[int | None]
    env_file: NotRequired[str | os.PathLike[str] | None]
    log_config: NotRequired[
        dict[str, Any] | str | os.PathLike[str] | RawConfigParser | IO[Any] | None
    ]
    log_level: NotRequired[str | int | None]
    access_log: NotRequired[bool]
    proxy_headers: NotRequired[bool]
    server_header: NotRequired[bool]
    date_header: NotRequired[bool]
    forwarded_allow_ips: NotRequired[list[str] | str | None]
    root_path: NotRequired[str]
    limit_concurrency: NotRequired[int | None]
    backlog: NotRequired[int]
    limit_max_requests: NotRequired[int | None]
    limit_max_requests_jitter: NotRequired[int]
    timeout_keep_alive: NotRequired[int]
    timeout_graceful_shutdown: NotRequired[int | None]
    timeout_worker_healthcheck: NotRequired[int]
    ssl_keyfile: NotRequired[str | os.PathLike[str] | None]
    ssl_certfile: NotRequired[str | os.PathLike[str] | None]
    ssl_keyfile_password: NotRequired[str | None]
    ssl_version: NotRequired[int]
    ssl_cert_reqs: NotRequired[int]
    ssl_ca_certs: NotRequired[str | os.PathLike[str] | None]
    ssl_ciphers: NotRequired[str | None]
    ssl_context_factory: NotRequired[
        Callable[[Config, Callable[[], ssl.SSLContext]], ssl.SSLContext] | None
    ]
    headers: NotRequired[list[tuple[str, str]] | None]
    use_colors: NotRequired[bool | None]
    app_dir: NotRequired[str | None]
    factory: NotRequired[bool]
    h11_max_incomplete_event_size: NotRequired[int | None]
    reset_contextvars: NotRequired[bool]


class PreStartFunc(Protocol):
    def __call__(
        self, host: str, port: int | None, reload: bool, docs_params: dict[str, str] | None = None
    ) -> Any: ...


class TyperSecho(Protocol):
    def __call__(self, message: str, bold: bool) -> Any: ...
