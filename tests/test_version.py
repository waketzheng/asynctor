import subprocess

from asynctor import __version__


def test_version():
    r = subprocess.run(["pdm", "list", "--fields=name,version", "--csv"], capture_output=True)
    out = r.stdout.decode().strip()
    try:
        me = [j for i in out.splitlines() if (j := i.split(","))[0] == "asynctor"][0]
    except IndexError:
        print("------ out:")
        print(out)
        print("^" * 20)
        from pathlib import Path

        assert __version__ in Path("asynctor/__init__.py").read_text()

    else:
        assert me[-1] == __version__
