from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated

import pytest
import typer
from fastapi import FastAPI

from asynctor.compat import chdir
from asynctor.contrib.fastapi import RunServer, runserver
from asynctor.utils import get_machine_ip


@pytest.fixture
def mock_uvicorn_run(mocker):
    mock_object = mocker.patch("uvicorn.run")
    yield mock_object


@dataclass
class CliOpts:
    addrport: Annotated[str | None, "Optional port number, or ipaddr:port"] = None
    port: int | None = None
    host: str = "0.0.0.0"
    reload: bool = False
    prod: bool = False
    verbose: bool = False

    def as_dict(self):
        return asdict(self)


def test_no_args(mock_uvicorn_run, mocker):
    mocker.patch.object(sys, "argv", sys.argv[:1])
    app = FastAPI()
    runserver(app)
    mock_uvicorn_run.assert_called_once_with(app, host="0.0.0.0", reload=False)


def test_reload(mock_uvicorn_run):
    opts = CliOpts(reload=True)
    RunServer.run(FastAPI(), echo=typer.secho, **opts.as_dict())
    mock_uvicorn_run.assert_called_once_with("__main__:app", host="0.0.0.0", reload=True)


def test_host(mock_uvicorn_run):
    host = "127.0.0.1"
    _test_host(mock_uvicorn_run, host)


def _test_host(mock_uvicorn_run, host):
    app = FastAPI()
    opts = CliOpts(host=host)
    RunServer.run(app, echo=typer.secho, **opts.as_dict())
    mock_uvicorn_run.assert_called_once_with(app, host=host, reload=False)


def test_host_ip(mock_uvicorn_run):
    host = get_machine_ip()
    _test_host(mock_uvicorn_run, host)


def test_host_domain(mock_uvicorn_run):
    host = "example.com"
    _test_host(mock_uvicorn_run, host)


def test_prod(mock_uvicorn_run):
    opts = CliOpts(prod=True)
    app = FastAPI()
    RunServer.run(app, echo=typer.secho, **opts.as_dict())
    mock_uvicorn_run.assert_called_once_with(app, host=opts.host, reload=False)


def test_prod_hint(mock_uvicorn_run):
    opts = CliOpts(prod=True)
    app = FastAPI()
    with chdir(Path(__file__).parent):
        RunServer.run(app, echo=typer.secho, **opts.as_dict())
    mock_uvicorn_run.assert_called_once_with(app, host=opts.host, port=9001, reload=False)


def test_port(mock_uvicorn_run):
    opts = CliOpts(port=9001)
    app = FastAPI()
    RunServer.run(app, echo=typer.secho, **opts.as_dict())
    mock_uvicorn_run.assert_called_once_with(app, host=opts.host, port=9001, reload=False)


def test_addrport(mock_uvicorn_run):
    opts = CliOpts(addrport="9001")
    app = FastAPI()
    RunServer.run(app, echo=typer.secho, **opts.as_dict())
    mock_uvicorn_run.assert_called_once_with(app, host=opts.host, port=9001, reload=False)


def test_addrport_localhost(mock_uvicorn_run):
    opts = CliOpts(addrport=":9001")
    app = FastAPI()
    RunServer.run(app, echo=typer.secho, **opts.as_dict())
    mock_uvicorn_run.assert_called_once_with(app, host="127.0.0.1", port=9001, reload=False)


def test_addrport_zero_host(mock_uvicorn_run):
    opts = CliOpts(addrport="0:9001")
    app = FastAPI()
    RunServer.run(app, echo=typer.secho, **opts.as_dict())
    mock_uvicorn_run.assert_called_once_with(app, host="0.0.0.0", port=9001, reload=False)


def test_addrport_ip_host(mock_uvicorn_run):
    host = get_machine_ip()
    opts = CliOpts(addrport=f"{host}:9001")
    app = FastAPI()
    RunServer.run(app, echo=typer.secho, **opts.as_dict())
    mock_uvicorn_run.assert_called_once_with(app, host=host, port=9001, reload=False)


def test_noreload(mocker):
    mocker.patch.object(sys, "argv", [sys.argv[0], "--noreload"])
    mock_object = mocker.patch("typer.run")
    runserver(FastAPI())
    assert sys.argv[1] == "--no-reload"
    mock_object.assert_called_once()
