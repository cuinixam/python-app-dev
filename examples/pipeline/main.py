import json
from abc import ABC
from dataclasses import dataclass
from pathlib import Path

from mashumaro import DataClassDictMixin

from py_app_dev.core.pipeline import PipelineConfig, PipelineLoader
from py_app_dev.core.runnable import Executor, Runnable


@dataclass
class ExecutionEnvironment:
    project_root_dir: Path
    output_dir: Path


class PipelineStep(Runnable, ABC):
    def __init__(self, environment: ExecutionEnvironment, group_name: str) -> None:
        self.environment = environment
        self.output_dir = self.environment.output_dir / group_name

    @property
    def project_root_dir(self) -> Path:
        return self.environment.project_root_dir


@dataclass
class MyConfig(DataClassDictMixin):
    pipeline: PipelineConfig


def main() -> None:
    this_dir = Path(__file__).parent
    my_config = MyConfig.from_dict(
        json.loads(this_dir.joinpath("config.json").read_text())
    )
    loader = PipelineLoader[PipelineStep](my_config.pipeline, this_dir)
    steps_references = loader.load_steps()
    for step_reference in steps_references:
        execution_environment = ExecutionEnvironment(this_dir, this_dir / "build")
        # Create step instance
        step = step_reference._class(execution_environment, step_reference.group_name)
        step.output_dir.mkdir(parents=True, exist_ok=True)
        # Execute step - see the files created in the 'build' directory!
        Executor(step.output_dir).execute(step)


if __name__ == "__main__":
    main()
