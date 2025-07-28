from pathlib import Path

from main import ExecutionEnvironment, PipelineStep

from py_app_dev.core.logging import logger


class MyBaseStep(PipelineStep):
    def __init__(self, environment: ExecutionEnvironment, group_name: str) -> None:
        super().__init__(environment, group_name)
        self.logger = logger.bind(step_name=self.get_name())


class MyInstallStep(MyBaseStep):
    def run(self) -> int:
        self.logger.info(f"Running {self.__class__.__name__} step. Output dir: {self.output_dir}")
        return 0

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_inputs(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return []


class MyRunStep(MyBaseStep):
    @property
    def output_file(self) -> Path:
        return self.output_dir / "output.txt"

    def run(self) -> int:
        self.logger.info(f"Running {self.__class__.__name__} step. Output dir: {self.output_dir}")
        self.output_file.write_text("Hello, World!")
        return 0

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_inputs(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return [self.output_file]
