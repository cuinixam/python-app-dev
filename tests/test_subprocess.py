from pathlib import Path

from py_app_dev.core.subprocess import SubprocessExecutor, which


def test_get_app_path():
    assert which("python")


def test_subprocess_executor(tmp_path: Path) -> None:
    SubprocessExecutor(["python", "-V"], cwd=tmp_path, capture_output=True).execute()
