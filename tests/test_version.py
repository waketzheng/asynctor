import subprocess

from asynctor import __version__


def test_version():
    r = subprocess.run(["pdm", "list", "--fields=name,version", "--csv"], capture_output=True)
    out = r.stdout.decode().strip()
    me = [j for i in out.splitlines() if (j := i.split(","))[0] == "asynctor"][0]
    assert me[-1] == __version__
