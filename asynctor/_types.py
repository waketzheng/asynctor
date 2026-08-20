from __future__ import annotations

import asyncio
import os
import ssl
from collections.abc import Callable, Mapping
from configparser import RawConfigParser
from typing import IO, TYPE_CHECKING, Any, Protocol, TypedDict

if TYPE_CHECKING:
    from ssl import TLSVersion, VerifyFlags, VerifyMode

    from redis.asyncio.connection import ConnectionPool
    from redis.asyncio.retry import Retry
    from redis.credentials import CredentialProvider
    from redis.driver_info import DriverInfo
    from redis.event import EventDispatcher
    from redis.maint_notifications import MaintNotificationsConfig
    from uvicorn.config import (
        Config,
        HTTPProtocolType,
        InterfaceType,
        LifespanType,
        LoopFactoryType,
        WSProtocolType,
    )


class UvicornKwargs(TypedDict, total=False):
    uds: str | None
    fd: int | None
    loop: LoopFactoryType | str
    http: type[asyncio.Protocol] | HTTPProtocolType | str
    ws: type[asyncio.Protocol] | WSProtocolType | str
    ws_max_size: int
    ws_max_queue: int
    ws_ping_interval: float | None
    ws_ping_timeout: float | None
    ws_per_message_deflate: bool
    lifespan: LifespanType
    interface: InterfaceType
    reload_dirs: list[str] | str | None
    reload_includes: list[str] | str | None
    reload_excludes: list[str] | str | None
    reload_delay: float
    workers: int | None
    env_file: str | os.PathLike[str] | None
    log_config: dict[str, Any] | str | os.PathLike[str] | RawConfigParser | IO[Any] | None
    log_level: str | int | None
    access_log: bool
    proxy_headers: bool
    server_header: bool
    date_header: bool
    forwarded_allow_ips: list[str] | str | None
    root_path: str
    limit_concurrency: int | None
    backlog: int
    limit_max_requests: int | None
    limit_max_requests_jitter: int
    timeout_keep_alive: int
    timeout_graceful_shutdown: int | None
    timeout_worker_healthcheck: int
    ssl_keyfile: str | os.PathLike[str] | None
    ssl_certfile: str | os.PathLike[str] | None
    ssl_keyfile_password: str | None
    ssl_version: int
    ssl_cert_reqs: int
    ssl_ca_certs: str | os.PathLike[str] | None
    ssl_ciphers: str | None
    ssl_context_factory: Callable[[Config, Callable[[], ssl.SSLContext]], ssl.SSLContext] | None
    headers: list[tuple[str, str]] | None
    use_colors: bool | None
    app_dir: str | None
    factory: bool
    h11_max_incomplete_event_size: int | None
    reset_contextvars: bool


class RedisKwargs(TypedDict, total=False):
    host: str
    port: int
    db: str | int
    password: str | None
    socket_timeout: float | None
    socket_connect_timeout: float | None
    socket_read_size: int
    socket_keepalive: bool | None
    socket_keepalive_options: Mapping[int, int | bytes] | object | None
    connection_pool: ConnectionPool | None
    unix_socket_path: str | None
    encoding: str
    encoding_errors: str
    decode_responses: bool
    retry_on_timeout: bool
    retry: Retry
    retry_on_error: list | None
    ssl: bool
    ssl_keyfile: str | None
    ssl_certfile: str | None
    ssl_cert_reqs: str | VerifyMode
    ssl_include_verify_flags: list[VerifyFlags] | None
    ssl_exclude_verify_flags: list[VerifyFlags] | None
    ssl_ca_certs: str | None
    ssl_ca_data: str | None
    ssl_ca_path: str | None
    ssl_check_hostname: bool
    ssl_min_version: TLSVersion | None
    ssl_ciphers: str | None
    ssl_password: str | None
    max_connections: int | None
    single_connection_client: bool
    health_check_interval: int
    client_name: str | None
    lib_name: str | object | None
    lib_version: str | object | None
    driver_info: DriverInfo | object | None
    username: str | None
    auto_close_connection_pool: bool | None
    redis_connect_func: Callable | None
    credential_provider: CredentialProvider | None
    protocol: int | None
    legacy_responses: bool
    event_dispatcher: EventDispatcher | None
    maint_notifications_config: MaintNotificationsConfig | None


class PreStartFunc(Protocol):
    def __call__(
        self, host: str, port: int | None, reload: bool, docs_params: dict[str, str] | None = None
    ) -> Any: ...


class TyperSecho(Protocol):
    def __call__(self, message: str, bold: bool) -> Any: ...
