import shlex
import shutil
import subprocess
from pathlib import Path


def test_fixtures(tmp_work_dir):
    asset_dir = Path(__file__).parent / "assets" / "testing_fixtures"
    for p in asset_dir.glob("*.py"):
        dst = "conftest.py" if p.stem == "conftest_" else "."
        shutil.copy(p, dst)
    cmd = "pytest _tests.py"
    r = subprocess.run(shlex.split(cmd), capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0
    assert "error" not in r.stdout.lower()
