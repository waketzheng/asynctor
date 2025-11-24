from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest
import typer
from fastapi import FastAPI

from asynctor.contrib.fastapi import RunServer, runserver


def test_runserver(mocker, capsys):
    mocker.patch("fast_dev_cli.cli.cli")
    runserver(FastAPI())
    out = capsys.readouterr().out.strip()
    assert out.replace("--> ", "") == "fastapi dev"
    runserver(FastAPI(), port=8001)
    out = capsys.readouterr().out.strip()
    assert out.replace("--> ", "") == "fastapi dev"


def test_dev(capsys):
    runserver(FastAPI())
    out = capsys.readouterr().out.strip()
    assert out.replace("--> ", "") == "fastapi dev"


@pytest.fixture
def mock_uvicorn_run(mocker):
    mock_object = mocker.patch("uvicorn.run")
    yield mock_object


def test_no_args(mock_uvicorn_run, mocker):
    mocker.patch.object(sys, "argv", sys.argv[:1])
    app = FastAPI()
    runserver(app)
    mock_uvicorn_run.assert_called_once_with(app, host="0.0.0.0", reload=False)


class Tmp:
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
        **kw,
    ) -> None: ...


def test_reload(mocker, tmp_work_dir):
    mocker.patch.object(sys, "argv", [sys.argv[0], "--reload"])
    mock_object = mocker.patch("uvicorn.run")
    Path("main.py").write_text("from fastapi import FastAPI\napp=FastAPI()")
    RunServer.run(
        FastAPI(), None, None, "0.0.0.0", reload=True, prod=False, verbose=False, echo=typer.echo
    )
    mock_object.assert_called_once_with("__main__:app", host="0.0.0.0", reload=True)
