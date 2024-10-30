import subprocess

from asynctor import __version__


def test_version():
    r = subprocess.run(["poetry", "version", "-s"], capture_output=True)
    assert r.stdout.decode().strip().split()[-1] == __version__
