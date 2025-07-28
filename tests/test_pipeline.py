from collections import OrderedDict
from pathlib import Path
from typing import Any

import pytest

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.pipeline import PipelineLoader, PipelineStep, PipelineStepConfig


def test_load_unknown_step():
    with pytest.raises(UserNotificationException):
        PipelineLoader[PipelineStep]._load_steps("install", [PipelineStepConfig(step="StepIDontExist")], Path("."))


def test_load_step_from_file(my_python_file: Path) -> None:
    result = PipelineLoader[PipelineStep]._load_steps(
        "install",
        [PipelineStepConfig(step="MyStep", file=str(my_python_file), config={"data": "value"})],
        my_python_file.parent,
    )
    assert len(result) == 1
    assert result[0].group_name == "install"
    assert result[0]._class.__name__ == "MyStep"
    assert result[0].config == {"data": "value"}


class MyCustomPipelineStep:
    def run(self) -> int:
        return 0

    def get_dependencies(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return []


def test_load_module_step_builtin():
    module_name = "tests.test_pipeline"
    step_class_name = "MyCustomPipelineStep"
    result = PipelineLoader[MyCustomPipelineStep]._load_module_step(module_name, step_class_name)
    assert result == MyCustomPipelineStep


def test_load_pipeline_config_as_list(my_python_file: Path) -> None:
    # Define the pipeline configuration as a list
    pipeline_config = [PipelineStepConfig(step="MyStep", file=str(my_python_file), config={"data": "value"})]

    loader = PipelineLoader[PipelineStep](pipeline_config, my_python_file)
    steps = loader.load_steps()

    assert len(steps) == 1
    assert steps[0].group_name is None
    assert steps[0]._class.__name__ == "MyStep"
    assert steps[0].config == {"data": "value"}


def test_load_pipeline_config_as_ordereddict(my_python_file: Path) -> None:
    # Define the pipeline configuration as an OrderedDict
    pipeline_config = OrderedDict({"install": [PipelineStepConfig(step="MyStep", file=str(my_python_file), config={"data": "value"})]})

    loader = PipelineLoader[PipelineStep](pipeline_config, my_python_file)
    steps = loader.load_steps()

    assert len(steps) == 1
    assert steps[0].group_name == "install"
    assert steps[0]._class.__name__ == "MyStep"
    assert steps[0].config == {"data": "value"}


def test_invalid_pipeline_config() -> None:
    # Define an invalid pipeline configuration
    invalid_pipeline_config: Any = "InvalidConfig"

    with pytest.raises(UserNotificationException, match="Invalid pipeline configuration"):
        PipelineLoader[PipelineStep](invalid_pipeline_config, Path(".")).load_steps()
