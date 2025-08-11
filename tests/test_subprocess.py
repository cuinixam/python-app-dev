import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from py_app_dev.core.subprocess import SubprocessExecutor, which


def test_get_app_path():
    """Test the which function for finding executables in PATH."""
    assert which("python")


class TestSubprocessExecutor:
    """Test class for SubprocessExecutor functionality."""

    @patch("loguru._logger.Logger.info")
    @pytest.mark.parametrize(
        "capture_output,print_output,expected_stdout_empty,expected_log_count",
        [
            (True, True, False, ">=2"),  # Capture and print - should have stdout + log command + output
            (True, False, False, 1),  # Capture but don't print - should have stdout + log only command
            (False, True, True, 1),  # Don't capture but print - should have empty stdout + log only command
            (False, False, True, 1),  # Don't capture or print - should have empty stdout + log only command
        ],
    )
    def test_capture_output_and_logging_combinations(
        self, mock_info: Mock, capture_output: bool, print_output: bool, expected_stdout_empty: bool, expected_log_count: str | int
    ) -> None:
        """Test different combinations of capture_output and print_output parameters with logger verification."""
        # Arrange & Act
        mock_info.reset_mock()
        process = SubprocessExecutor(["python", "-V"], capture_output=capture_output, print_output=print_output).execute(handle_errors=False)

        # Assert process execution
        assert process and process.returncode == 0

        # Assert stdout behavior
        if expected_stdout_empty:
            assert process.stdout == ""
        else:
            assert "Python" in process.stdout

        # Assert logger behavior
        if expected_log_count == ">=2":
            # Should log both command execution and Python version output
            assert mock_info.call_count >= 2
            # Check that the command execution was logged
            command_logged = any("Running command: python -V" in str(call) for call in mock_info.call_args_list)
            assert command_logged, "Command execution should be logged"
            # Check that Python version output was logged
            python_output_logged = any("Python" in str(call) and "Running command" not in str(call) for call in mock_info.call_args_list)
            assert python_output_logged, "Python version output should be logged when print_output=True"
        else:
            # Should only log the command execution, not the output
            assert mock_info.call_count == expected_log_count
            assert "Running command: python -V" in str(mock_info.call_args_list[0])

    @pytest.mark.parametrize(
        "command, exp_stdout, exp_returncode",
        [
            (["python", "-c", "print('Hello World!')"], "Hello World!\n", 0),
            # SubprocessExecutor redirects stderr to stdout when capture_output=True
            (
                [
                    "python",
                    "-c",
                    "import sys; print('Hello World!', file=sys.stderr)",
                ],
                "Hello World!\n",
                0,
            ),
            (["python", "-c", "exit(0)"], "", 0),
            (["python", "-c", "exit(1)"], "", 1),
            (["python", "-c", "exit(42)"], "", 42),
        ],
    )
    def test_command_execution_scenarios(self, command, exp_stdout, exp_returncode):
        """Test various command execution scenarios adapted from CommandLineExecutor tests."""
        # Arrange
        executor = SubprocessExecutor(command, capture_output=True, print_output=False)

        # Act
        result = executor.execute(handle_errors=False)

        # Assert
        assert result is not None
        assert result.stdout == exp_stdout
        # Note: SubprocessExecutor redirects stderr to stdout, so stderr is always None
        # This is different from CommandLineExecutor which returned empty string for stderr
        assert result.stderr is None
        assert result.returncode == exp_returncode

    @pytest.mark.skipif(platform.system() != "Windows", reason="Junction creation test is Windows-specific")
    def test_junction_creation(self, tmp_path: Path) -> None:
        """Test creating a junction link (Windows-specific test adapted from CommandLineExecutor)."""
        # Arrange
        test_path = tmp_path.joinpath("test")
        test_path.mkdir()
        link_path = test_path.joinpath("link")
        command: list[str | Path] = ["cmd", "/c", "mklink", "/J", str(link_path), str(test_path)]
        executor = SubprocessExecutor(command, capture_output=True, print_output=False)

        # Act
        result = executor.execute(handle_errors=False)

        # Assert
        assert result is not None
        assert result.returncode == 0

    @pytest.mark.parametrize(
        "stream_type, test_data, expected_text_parts",
        [
            ("stdout", b"Hello\x85World\n", ["Hello", "World"]),
            ("stderr", b"Error\x85Message\n", ["Error", "Message"]),
        ],
    )
    def test_undecodable_bytes_handling(self, stream_type: str, test_data: bytes, expected_text_parts: list[str]) -> None:
        """Test that undecodable bytes in stdout/stderr are handled gracefully."""
        # Arrange
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp:
            # Write bytes that are invalid in UTF-8 (e.g., 0x85)
            tmp.write(test_data)
            tmp_path = tmp.name

        try:
            if stream_type == "stdout":
                py_cmd: list[str | Path] = ["python", "-c", f"import sys; sys.stdout.buffer.write(open(r'{tmp_path}', 'rb').read())"]
            else:  # stderr
                py_cmd = ["python", "-c", f"import sys; sys.stderr.buffer.write(open(r'{tmp_path}', 'rb').read())"]

            executor = SubprocessExecutor(py_cmd, capture_output=True, print_output=False)

            # Act
            result = executor.execute(handle_errors=False)

            # Assert
            assert result is not None
            for expected_part in expected_text_parts:
                assert expected_part in result.stdout
            # Should not raise UnicodeDecodeError due to errors="replace" in subprocess.py
            assert result.returncode == 0
        finally:
            os.remove(tmp_path)
