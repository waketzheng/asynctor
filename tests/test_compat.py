from pathlib import Path


def test_chdir(tmp_work_dir):
    assert tmp_work_dir == Path.cwd()
