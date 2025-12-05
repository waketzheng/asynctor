import shlex
import shutil
import subprocess
from pathlib import Path

from asynctor.testing import tmp_workdir_fixture


def test_fixtures(tmp_work_dir):
    asset_dir = Path(__file__).parent / "assets" / "testing_fixtures"
    for p in asset_dir.glob("*.py"):
        dst = "conftest.py" if p.stem == "conftest_" else "."
        shutil.copy(p, dst)
    cmd = "pytest _tests.py"
    r = subprocess.run(shlex.split(cmd), capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0
    assert "error" not in r.stdout.lower()


new_work_dir = tmp_workdir_fixture()
CURRENT_DIR = Path.cwd()


def test_pwd(new_work_dir):
    assert Path.cwd() != CURRENT_DIR
    assert not list(Path().glob("*"))
    temp_file = Path("a.txt")
    assert temp_file.write_bytes(b"1") == 1
    assert temp_file.read_text() == "1"
    temp_file.unlink()
    assert not temp_file.exists()
