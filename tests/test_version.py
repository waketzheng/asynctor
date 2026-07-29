import subprocess

from asynctor import __package__, __version__


def test_version():
    r = subprocess.run(["uv", "pip", "list"], capture_output=True, check=False)
    out = r.stdout.decode().strip()
    me = next(j for i in out.splitlines() if (j := i.split())[0] == __package__)
    assert me[1] == __version__
