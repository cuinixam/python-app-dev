import json
import os
from pathlib import Path

import pytest

from py_app_dev.core.runnable import Executor, RunInfoStatus, Runnable


class MyRunnable(Runnable):
    def __init__(
        self,
        inputs: list[Path] | None = None,
        outputs: list[Path] | None = None,
        return_code: int = 0,
        needs_dependency_management: bool = True,
    ) -> None:
        super().__init__(needs_dependency_management=needs_dependency_management)
        self._inputs = inputs if inputs is not None else []
        self._outputs = outputs if outputs is not None else []
        self._return_code = return_code

    def get_name(self) -> str:
        return self.__class__.__name__

    def run(self) -> int:
        return self._return_code

    def get_inputs(self) -> list[Path]:
        return self._inputs

    def get_outputs(self) -> list[Path]:
        return self._outputs


@pytest.fixture
def executor(tmp_path: Path) -> Executor:
    """Fixture for creating an Executor with a cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return Executor(cache_dir=cache_dir)


def test_no_previous_info(executor: Executor) -> None:
    """Test that Executor correctly detects that a runnable has not been executed before."""
    runnable = MyRunnable()
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.NO_INFO


def test_previous_info_matches(executor: Executor, tmp_path: Path) -> None:
    """Test that Executor correctly skips execution when previous info matches."""
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    input_path.write_text("input")
    output_path.write_text("output")
    runnable = MyRunnable(inputs=[input_path], outputs=[output_path])
    executor.execute(runnable)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH
    new_executor = Executor(cache_dir=executor.cache_dir, force_run=True)
    assert new_executor.previous_run_info_matches(runnable) == RunInfoStatus.FORCED_RUN


def test_file_changed(executor: Executor, tmp_path: Path) -> None:
    """Test that Executor correctly detects when a file has changed."""
    input_path = tmp_path / "input.txt"
    input_path.write_text("input")
    runnable = MyRunnable(inputs=[input_path])
    executor.execute(runnable)
    input_path.write_text("changed")
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.FILE_CHANGED


def test_file_removed(executor: Executor, tmp_path: Path) -> None:
    """Test that Executor correctly detects when a file has been removed."""
    output_path = tmp_path / "output.txt"
    output_path.write_text("output")
    runnable = MyRunnable(outputs=[output_path])
    executor.execute(runnable)
    os.remove(output_path)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.FILE_NOT_FOUND


def test_directory_exists(executor: Executor, tmp_path: Path) -> None:
    """Test that Executor correctly handles existing directories."""
    input_dir = tmp_path / "input_dir"
    output_dir = tmp_path / "output_dir"
    input_dir.mkdir()
    output_dir.mkdir()
    runnable = MyRunnable(inputs=[input_dir], outputs=[output_dir])
    executor.execute(runnable)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH


def test_directory_removed(executor: Executor, tmp_path: Path) -> None:
    """Test that Executor correctly detects when a directory has been removed."""
    input_dir = tmp_path / "input_dir"
    output_dir = tmp_path / "output_dir"
    input_dir.mkdir()
    output_dir.mkdir()
    runnable = MyRunnable(inputs=[input_dir], outputs=[output_dir])
    executor.execute(runnable)
    input_dir.rmdir()
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.FILE_NOT_FOUND


def test_mixed_files_and_directories(executor: Executor, tmp_path: Path) -> None:
    """Test that Executor correctly handles a mix of files and directories."""
    input_file = tmp_path / "input.txt"
    input_dir = tmp_path / "input_dir"
    output_file = tmp_path / "output.txt"
    output_dir = tmp_path / "output_dir"
    input_file.write_text("input")
    input_dir.mkdir()
    output_file.write_text("output")
    output_dir.mkdir()
    runnable = MyRunnable(inputs=[input_file, input_dir], outputs=[output_file, output_dir])
    executor.execute(runnable)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH


def test_no_inputs_and_no_outputs(executor: Executor) -> None:
    """Test that Executor correctly handles a runnable with no inputs and no outputs."""
    runnable = MyRunnable()
    executor.execute(runnable)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.NOTHING_TO_CHECK


def test_dry_run(executor: Executor) -> None:
    """Test that Executor does not execute the run method when dry_run is True."""
    runnable = MyRunnable(return_code=1)
    executor.dry_run = True
    assert executor.execute(runnable) == 0
    executor.dry_run = False
    assert executor.execute(runnable) == 1


def test_no_dependency_management(executor: Executor) -> None:
    """Test that Executor executes runnables without dependency management directly."""
    runnable = MyRunnable(needs_dependency_management=False, return_code=2)
    assert executor.execute(runnable) == 2
    # Ensure it doesn't store or check run info
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.NO_INFO


def test_config_changed(executor: Executor, tmp_path: Path) -> None:
    """Test that Executor detects when the configuration has changed."""
    input_path = tmp_path / "input.txt"
    input_path.write_text("input")

    class ConfigurableRunnable(MyRunnable):
        def __init__(
            self,
            config: dict[str, str],
            inputs: list[Path] | None = None,
        ) -> None:
            super().__init__(inputs=inputs)
            self._config = config

        def get_config(self) -> dict[str, str] | None:
            return self._config

    runnable = ConfigurableRunnable(config={"key": "value"}, inputs=[input_path])
    executor.execute(runnable)

    # Ensure it matches initially
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH

    # Change the configuration
    runnable = ConfigurableRunnable(config={"key": "new_value"}, inputs=[input_path])
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.CONFIG_CHANGED


def test_config_stored(executor: Executor, tmp_path: Path) -> None:
    """Test that Executor stores the configuration alongside inputs and outputs."""
    input_path = tmp_path / "input.txt"
    input_path.write_text("input")

    class ConfigurableRunnable(MyRunnable):
        def __init__(
            self,
            config: dict[str, str],
            inputs: list[Path] | None = None,
        ) -> None:
            super().__init__(inputs=inputs)
            self._config = config

        def get_config(self) -> dict[str, str] | None:
            return self._config

    config = {"key": "value"}
    runnable = ConfigurableRunnable(config=config, inputs=[input_path])
    executor.execute(runnable)

    # Verify the stored run info contains the configuration
    run_info_path = executor.get_runnable_run_info_file(runnable)
    with run_info_path.open() as f:
        run_info = json.load(f)
    assert run_info["config"] == config


def test_config_not_stored_if_none(executor: Executor, tmp_path: Path) -> None:
    """Test that Executor does not store a config if the runnable has no config."""
    input_path = tmp_path / "input.txt"
    input_path.write_text("input")

    runnable = MyRunnable(inputs=[input_path])
    executor.execute(runnable)

    # Verify the stored run info does not contain a config field
    run_info_path = executor.get_runnable_run_info_file(runnable)
    with run_info_path.open() as f:
        run_info = json.load(f)
    assert "config" not in run_info
