import os
from pathlib import Path
from typing import List

import pytest

from py_app_dev.core.runnable import Executor, RunInfoStatus, Runnable


class MyRunnable(Runnable):
    def __init__(self, name: str, inputs: List[Path] = [], outputs: List[Path] = []):
        self._name = name
        self._inputs = inputs
        self._outputs = outputs

    def get_name(self) -> str:
        return self._name

    def run(self) -> int:
        return 0

    def get_inputs(self) -> List[Path]:
        return self._inputs

    def get_outputs(self) -> List[Path]:
        return self._outputs


@pytest.fixture
def executor(tmp_path):
    """Fixture for creating an Executor with a cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return Executor(cache_dir=cache_dir)


def test_no_previous_info(executor):
    """Test that Executor correctly detects that a runnable has not been executed before."""
    runnable = MyRunnable(name="test1")
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.NO_INFO


def test_previous_info_matches(executor, tmp_path):
    """Test that Executor correctly skips execution when previous info matches."""
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    input_path.write_text("input")
    output_path.write_text("output")
    runnable = MyRunnable(name="test2", inputs=[input_path], outputs=[output_path])
    executor.execute(runnable)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH


def test_file_changed(executor, tmp_path):
    """Test that Executor correctly detects when a file has changed."""
    input_path = tmp_path / "input.txt"
    input_path.write_text("input")
    runnable = MyRunnable(name="test3", inputs=[input_path])
    executor.execute(runnable)
    input_path.write_text("changed")
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.FILE_CHANGED


def test_file_removed(executor, tmp_path):
    """Test that Executor correctly detects when a file has been removed."""
    output_path = tmp_path / "output.txt"
    output_path.write_text("output")
    runnable = MyRunnable(name="test4", outputs=[output_path])
    executor.execute(runnable)
    os.remove(output_path)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.FILE_NOT_FOUND


def test_directory_exists(executor, tmp_path):
    """Test that Executor correctly handles existing directories."""
    input_dir = tmp_path / "input_dir"
    output_dir = tmp_path / "output_dir"
    input_dir.mkdir()
    output_dir.mkdir()
    runnable = MyRunnable(name="test5", inputs=[input_dir], outputs=[output_dir])
    executor.execute(runnable)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH


def test_directory_removed(executor, tmp_path):
    """Test that Executor correctly detects when a directory has been removed."""
    input_dir = tmp_path / "input_dir"
    output_dir = tmp_path / "output_dir"
    input_dir.mkdir()
    output_dir.mkdir()
    runnable = MyRunnable(name="test6", inputs=[input_dir], outputs=[output_dir])
    executor.execute(runnable)
    input_dir.rmdir()
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.FILE_NOT_FOUND


def test_mixed_files_and_directories(executor, tmp_path):
    """Test that Executor correctly handles a mix of files and directories."""
    input_file = tmp_path / "input.txt"
    input_dir = tmp_path / "input_dir"
    output_file = tmp_path / "output.txt"
    output_dir = tmp_path / "output_dir"
    input_file.write_text("input")
    input_dir.mkdir()
    output_file.write_text("output")
    output_dir.mkdir()
    runnable = MyRunnable(
        name="test7", inputs=[input_file, input_dir], outputs=[output_file, output_dir]
    )
    executor.execute(runnable)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH


def test_no_inputs_and_no_outputs(executor):
    """Test that Executor correctly handles a runnable with no inputs and no outputs."""
    runnable = MyRunnable(name="test8")
    executor.execute(runnable)
    assert (
        executor.previous_run_info_matches(runnable) == RunInfoStatus.NOTHING_TO_CHECK
    )
