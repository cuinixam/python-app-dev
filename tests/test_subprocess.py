from pathlib import Path

from py_app_dev.core.subprocess import SubprocessExecutor, which


def test_get_app_path():
    assert which("python")


def test_subprocess_executor(tmp_path: Path) -> None:
    SubprocessExecutor(["python", "-V"], cwd=tmp_path, capture_output=True).execute()


def test_subprocess_executor_no_error_handling() -> None:
    process = SubprocessExecutor(["python", "-V"], capture_output=True).execute(handle_errors=False)
    assert process and process.returncode == 0
    assert process.stdout == ""
    process = SubprocessExecutor(["python", "-V"], capture_output=True, print_output=False).execute(handle_errors=False)
    assert process and process.returncode == 0
    assert "Python" in process.stdout
