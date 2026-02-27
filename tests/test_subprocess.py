import platform
import time
from pathlib import Path
from unittest.mock import Mock, patch

import psutil
import pytest

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.subprocess import SubprocessExecutor, which

_SLEEP_CMD: list[str | Path] = ["python", "-c", "import time; time.sleep(30)"]
_TIMEOUT_SECONDS: int = 2


def test_get_app_path() -> None:
    assert which("python")


@patch("loguru._logger.Logger.info")
@pytest.mark.parametrize(
    "capture_output,print_output,expected_stdout_empty,expected_log_count",
    [
        (True, True, False, ">=2"),
        (True, False, False, 1),
        (False, True, True, 1),
        (False, False, True, 1),
    ],
)
def test_capture_output_and_logging_combinations(mock_info: Mock, capture_output: bool, print_output: bool, expected_stdout_empty: bool, expected_log_count: str | int) -> None:
    mock_info.reset_mock()
    process = SubprocessExecutor(["python", "-V"], capture_output=capture_output, print_output=print_output).execute(handle_errors=False)

    assert process and process.returncode == 0

    if expected_stdout_empty:
        assert process.stdout == ""
    else:
        assert "Python" in process.stdout

    if expected_log_count == ">=2":
        assert mock_info.call_count >= 2
        command_logged = any("Running command: python -V" in str(call) for call in mock_info.call_args_list)
        assert command_logged, "Command execution should be logged"
        python_output_logged = any("Python" in str(call) and "Running command" not in str(call) for call in mock_info.call_args_list)
        assert python_output_logged, "Python version output should be logged when print_output=True"
    else:
        assert mock_info.call_count == expected_log_count
        assert "Running command: python -V" in str(mock_info.call_args_list[0])


@pytest.mark.parametrize(
    "command, exp_stdout, exp_returncode",
    [
        (["python", "-c", "print('Hello World!')"], "Hello World!\n", 0),
        (
            ["python", "-c", "import sys; print('Hello World!', file=sys.stderr)"],
            "Hello World!\n",
            0,
        ),
        (["python", "-c", "exit(0)"], "", 0),
        (["python", "-c", "exit(1)"], "", 1),
        (["python", "-c", "exit(42)"], "", 42),
    ],
)
def test_command_execution_scenarios(command: list[str | Path], exp_stdout: str, exp_returncode: int) -> None:
    result = SubprocessExecutor(command, capture_output=True, print_output=False).execute(handle_errors=False)
    assert result is not None
    assert result.stdout == exp_stdout
    assert result.stderr is None
    assert result.returncode == exp_returncode


@pytest.mark.skipif(platform.system() != "Windows", reason="Junction creation test is Windows-specific")
def test_junction_creation(tmp_path: Path) -> None:
    test_path = tmp_path / "test"
    test_path.mkdir()
    link_path = test_path / "link"
    command: list[str | Path] = ["cmd", "/c", "mklink", "/J", str(link_path), str(test_path)]
    result = SubprocessExecutor(command, capture_output=True, print_output=False).execute(handle_errors=False)
    assert result is not None
    assert result.returncode == 0


def test_file_not_found_raises_user_notification_exception() -> None:
    with pytest.raises(UserNotificationException, match="could not be executed"):
        SubprocessExecutor(["nonexistent_command_xyz_abc"]).execute()


def test_keyboard_interrupt_raises_user_notification_exception() -> None:
    with patch("subprocess.Popen.wait", side_effect=KeyboardInterrupt):
        with pytest.raises(UserNotificationException, match="interrupted by user"):
            SubprocessExecutor(["python", "-V"], capture_output=False).execute()


@pytest.mark.parametrize(
    "stream_type, test_data, expected_text_parts",
    [
        ("stdout", b"Hello\x85World\n", ["Hello", "World"]),
        ("stderr", b"Error\x85Message\n", ["Error", "Message"]),
    ],
)
def test_undecodable_bytes_handling(tmp_path: Path, stream_type: str, test_data: bytes, expected_text_parts: list[str]) -> None:
    tmp_file = tmp_path / "test_data.bin"
    tmp_file.write_bytes(test_data)
    if stream_type == "stdout":
        py_cmd: list[str | Path] = ["python", "-c", f"import sys; sys.stdout.buffer.write(open(r'{tmp_file}', 'rb').read())"]
    else:
        py_cmd = ["python", "-c", f"import sys; sys.stderr.buffer.write(open(r'{tmp_file}', 'rb').read())"]
    result = SubprocessExecutor(py_cmd, capture_output=True, print_output=False).execute(handle_errors=False)
    assert result is not None
    for expected_part in expected_text_parts:
        assert expected_part in result.stdout
    assert result.returncode == 0


@pytest.mark.parametrize(
    "capture_output, print_output",
    [
        (True, False),
        (True, True),
        (False, False),
    ],
)
def test_timeout_raises_user_notification_exception(capture_output: bool, print_output: bool) -> None:
    executor = SubprocessExecutor(
        _SLEEP_CMD,
        capture_output=capture_output,
        print_output=print_output,
        timeout=_TIMEOUT_SECONDS,
    )
    start = time.monotonic()
    with pytest.raises(UserNotificationException, match="timed out"):
        executor.execute()
    elapsed = time.monotonic() - start
    assert elapsed < 5, f"Timeout should fire within ~2 s but took {elapsed:.1f} s"


@pytest.mark.parametrize("print_output", [False, True])
def test_timeout_kills_process_tree(tmp_path: Path, print_output: bool) -> None:
    pid_file = tmp_path / "child_pid.txt"
    script = tmp_path / "spawn_child.py"
    script.write_text(
        "import subprocess, sys, time\n"
        f"child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        f"open(r'{pid_file}', 'w').write(str(child.pid))\n"
        "time.sleep(30)\n"
    )
    executor = SubprocessExecutor(
        ["python", str(script)],
        capture_output=True,
        print_output=print_output,
        timeout=_TIMEOUT_SECONDS,
    )
    with pytest.raises(UserNotificationException, match="timed out"):
        executor.execute()
    time.sleep(0.5)
    assert pid_file.exists(), "Child PID file must exist; the script must have run long enough to write it"
    child_pid = int(pid_file.read_text().strip())
    assert not psutil.pid_exists(child_pid), f"Child process {child_pid} should have been killed by _terminate_process_tree"


def test_streaming_timeout_blocked_by_silent_process() -> None:
    """Reproduces the bug where readline() blocks indefinitely when the process is alive but writes nothing to stdout."""
    executor = SubprocessExecutor(
        ["python", "-c", "import time; time.sleep(10)"],
        capture_output=True,
        print_output=True,
        timeout=2,
    )
    start = time.monotonic()
    with pytest.raises(UserNotificationException, match="timed out"):
        executor.execute()
    elapsed = time.monotonic() - start
    assert elapsed < 5, f"Timeout should fire within ~2 s but took {elapsed:.1f} s"


@pytest.mark.parametrize(
    "capture_output, print_output",
    [
        (True, False),
        (True, True),
        (False, False),
    ],
)
def test_fast_command_is_unaffected_by_timeout(capture_output: bool, print_output: bool) -> None:
    executor = SubprocessExecutor(
        ["python", "-c", "print('done')"],
        capture_output=capture_output,
        print_output=print_output,
        timeout=30,
    )
    result = executor.execute(handle_errors=False)
    assert result is not None
    assert result.returncode == 0
