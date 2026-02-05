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
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return Executor(cache_dir=cache_dir)


def test_no_previous_info(executor: Executor) -> None:
    runnable = MyRunnable()
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.NO_INFO


def test_previous_info_matches(executor: Executor, tmp_path: Path) -> None:
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
    input_path = tmp_path / "input.txt"
    input_path.write_text("input")
    runnable = MyRunnable(inputs=[input_path])
    executor.execute(runnable)
    input_path.write_text("changed")
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.FILE_CHANGED


def test_file_removed(executor: Executor, tmp_path: Path) -> None:
    output_path = tmp_path / "output.txt"
    output_path.write_text("output")
    runnable = MyRunnable(outputs=[output_path])
    executor.execute(runnable)
    os.remove(output_path)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.FILE_NOT_FOUND


def test_directory_exists(executor: Executor, tmp_path: Path) -> None:
    input_dir = tmp_path / "input_dir"
    output_dir = tmp_path / "output_dir"
    input_dir.mkdir()
    output_dir.mkdir()
    runnable = MyRunnable(inputs=[input_dir], outputs=[output_dir])
    executor.execute(runnable)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH


def test_directory_removed(executor: Executor, tmp_path: Path) -> None:
    input_dir = tmp_path / "input_dir"
    output_dir = tmp_path / "output_dir"
    input_dir.mkdir()
    output_dir.mkdir()
    runnable = MyRunnable(inputs=[input_dir], outputs=[output_dir])
    executor.execute(runnable)
    input_dir.rmdir()
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.FILE_NOT_FOUND


def test_mixed_files_and_directories(executor: Executor, tmp_path: Path) -> None:
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
    runnable = MyRunnable()
    executor.execute(runnable)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.NOTHING_TO_CHECK


def test_dry_run(executor: Executor) -> None:
    runnable = MyRunnable(return_code=1)
    executor.dry_run = True
    assert executor.execute(runnable) == 0
    executor.dry_run = False
    assert executor.execute(runnable) == 1


def test_no_dependency_management(executor: Executor) -> None:
    runnable = MyRunnable(needs_dependency_management=False, return_code=2)
    assert executor.execute(runnable) == 2
    # Ensure it doesn't store or check run info
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.NO_INFO


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


def test_config_changed(executor: Executor, tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    input_path.write_text("input")

    runnable = ConfigurableRunnable(config={"key": "value"}, inputs=[input_path])
    executor.execute(runnable)

    # Ensure it matches initially
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH

    # Change the configuration
    runnable = ConfigurableRunnable(config={"key": "new_value"}, inputs=[input_path])
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.CONFIG_CHANGED


def test_config_stored(executor: Executor, tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    input_path.write_text("input")

    config = {"key": "value"}
    runnable = ConfigurableRunnable(config=config, inputs=[input_path])
    executor.execute(runnable)

    # Verify the stored run info contains the configuration
    run_info_path = executor.get_runnable_run_info_file(runnable)
    with run_info_path.open() as f:
        run_info = json.load(f)
    assert run_info["config"] == config


def test_config_not_stored_if_none(executor: Executor, tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    input_path.write_text("input")

    runnable = MyRunnable(inputs=[input_path])
    executor.execute(runnable)

    # Verify the stored run info does not contain a config field
    run_info_path = executor.get_runnable_run_info_file(runnable)
    with run_info_path.open() as f:
        run_info = json.load(f)
    assert "config" not in run_info


class DynamicInputRunnable(MyRunnable):
    def __init__(self, input_dir: Path) -> None:
        super().__init__()
        self.input_dir = input_dir

    def get_inputs(self) -> list[Path]:
        # Simulates a runnable that parses all .yaml files from a directory
        return list(self.input_dir.glob("*.yaml"))


def test_new_input_files_trigger_execution(executor: Executor, tmp_path: Path) -> None:
    input_dir = tmp_path / "configs"
    input_dir.mkdir()

    # Create initial yaml file
    yaml_file1 = input_dir / "config1.yaml"
    yaml_file1.write_text("config: value1")

    runnable = DynamicInputRunnable(input_dir)

    # First execution should run (no previous info)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.NO_INFO
    executor.execute(runnable)

    # Second execution should be skipped (nothing changed)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH

    # Create a new yaml file - this should trigger re-execution
    yaml_file2 = input_dir / "config2.yaml"
    yaml_file2.write_text("config: value2")

    # This should detect the new input file and require re-execution
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.INPUT_FILES_CHANGED


def test_removed_input_files_trigger_execution(executor: Executor, tmp_path: Path) -> None:
    input_dir = tmp_path / "configs"
    input_dir.mkdir()

    # Create initial yaml files
    yaml_file1 = input_dir / "config1.yaml"
    yaml_file1.write_text("config: value1")
    yaml_file2 = input_dir / "config2.yaml"
    yaml_file2.write_text("config: value2")

    runnable = DynamicInputRunnable(input_dir)

    # First execution should run (no previous info)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.NO_INFO
    executor.execute(runnable)

    # Second execution should be skipped (nothing changed)
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.MATCH

    # Remove one yaml file - this should trigger re-execution
    yaml_file2.unlink()

    # This should detect the missing input file and require re-execution
    assert executor.previous_run_info_matches(runnable) == RunInfoStatus.INPUT_FILES_CHANGED


class CustomIdRunnable(MyRunnable):
    """Runnable with custom get_id() for unique identification."""

    def __init__(self, custom_id: str) -> None:
        super().__init__()
        self._custom_id = custom_id

    def get_id(self) -> str:
        return f"{self.get_name()}_{self._custom_id}"


def test_get_id_defaults_to_get_name() -> None:
    runnable = MyRunnable()
    assert runnable.get_id() == runnable.get_name()


def test_custom_get_id_produces_unique_deps_files(executor: Executor) -> None:
    runnable1 = CustomIdRunnable(custom_id="first")
    runnable2 = CustomIdRunnable(custom_id="second")

    # Different IDs should produce different deps file paths
    path1 = executor.get_runnable_run_info_file(runnable1)
    path2 = executor.get_runnable_run_info_file(runnable2)

    assert path1 != path2
    assert "first" in str(path1)
    assert "second" in str(path2)


def test_custom_get_id_deps_files_are_independent(executor: Executor, tmp_path: Path) -> None:
    input_file = tmp_path / "input.txt"
    input_file.write_text("content")

    runnable1 = CustomIdRunnable(custom_id="first")
    runnable1._inputs = [input_file]
    runnable2 = CustomIdRunnable(custom_id="second")
    runnable2._inputs = [input_file]

    # Execute first runnable
    executor.execute(runnable1)
    assert executor.previous_run_info_matches(runnable1) == RunInfoStatus.MATCH

    # Second runnable should still need to run (no previous info for its ID)
    assert executor.previous_run_info_matches(runnable2) == RunInfoStatus.NO_INFO
