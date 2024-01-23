import importlib
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import List, Optional, OrderedDict, Type, TypeAlias

from mashumaro import DataClassDictMixin

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from py_app_dev.core.runnable import Executor, Runnable


@dataclass
class StageConfig(DataClassDictMixin):
    #: Stage name or class name if file is not specified
    stage: str
    #: Path to file with stage class
    file: Optional[str] = None
    #: Python module with stage class
    module: Optional[str] = None
    #: Stage class name
    class_name: Optional[str] = None
    #: Stage description
    description: Optional[str] = None
    #: Stage timeout in seconds
    timeout_sec: Optional[int] = None


PipelineConfig: TypeAlias = OrderedDict[str, List[StageConfig]]


class Context(ABC):
    """Holds all context to run a stage.
    Information might be inserted by a stage to be available to the subsequent stages.
    """

    @property
    @abstractmethod
    def project_root_dir(self) -> Path:
        ...

    @property
    @abstractmethod
    def output_dir(self) -> Path:
        ...

    @abstractmethod
    def is_clean_required(self) -> bool:
        ...


class Stage(Runnable, ABC):
    def __init__(self, context: Context, output_dir: Path) -> None:
        self.context = context
        self.output_dir = output_dir

    @property
    def project_root_dir(self) -> Path:
        return self.context.project_root_dir


@dataclass
class StageReference:
    """Once a Stage is found, keep the Stage class reference to be able to instantiate it later."""

    group_name: str
    _class: Type[Stage]


class PipelineLoader:
    def __init__(self, pipeline_config: PipelineConfig, project_root_dir: Path) -> None:
        self.pipeline_config = pipeline_config
        self.project_root_dir = project_root_dir

    def load_stages(self) -> List[StageReference]:
        result = []
        for group_name, stages_config in self.pipeline_config.items():
            result.extend(
                self._load_stages(group_name, stages_config, self.project_root_dir)
            )
        return result

    @staticmethod
    def _load_stages(
        group_name: str, stages_config: List[StageConfig], project_root_dir: Path
    ) -> List[StageReference]:
        result = []
        for stage_config in stages_config:
            stage_class_name = stage_config.class_name or stage_config.stage
            if stage_config.module:
                stage_class = PipelineLoader._load_module_stage(
                    stage_config.module, stage_class_name
                )
            elif stage_config.file:
                stage_class = PipelineLoader._load_user_stage(
                    project_root_dir.joinpath(stage_config.file), stage_class_name
                )
            else:
                raise UserNotificationException(
                    f"Stage '{stage_class_name}' has no 'module' nor 'file' defined."
                    " Please check your pipeline configuration."
                )
            result.append(StageReference(group_name, stage_class))
        return result

    @staticmethod
    def _load_user_stage(python_file: Path, stage_class_name: str) -> Type[Stage]:
        # Create a module specification from the file path
        spec = spec_from_file_location(f"user__{stage_class_name}", python_file)
        if spec and spec.loader:
            stage_module = module_from_spec(spec)
            # Import the module
            spec.loader.exec_module(stage_module)
            try:
                stage_class = getattr(stage_module, stage_class_name)
            except AttributeError:
                raise UserNotificationException(
                    f"Could not load class '{stage_class_name}' from file '{python_file}'."
                    " Please check your pipeline configuration."
                )
            return stage_class
        raise UserNotificationException(
            f"Could not load file '{python_file}'."
            " Please check the file for any errors."
        )

    @staticmethod
    def _load_module_stage(module_name: str, stage_class_name: str) -> Type[Stage]:
        try:
            module = importlib.import_module(module_name)
            stage_class = getattr(module, stage_class_name)
        except ImportError:
            raise UserNotificationException(
                f"Could not load module '{module_name}'. Please check your pipeline configuration."
            )
        except AttributeError:
            raise UserNotificationException(
                f"Could not load class '{stage_class_name}' from module '{module_name}'."
                " Please check your pipeline configuration."
            )
        return stage_class


class StageRunner:
    """It checks if a stage must run in current environment.
    A stage shall run if any of the dependencies changed or one of the outputs is missing.
    All dependencies and outputs relevant information is stored in the stage output directory
    in a <stage>.deps file.
    """

    def __init__(
        self, context: Context, stages_references: List[StageReference]
    ) -> None:
        self.logger = logger.bind()
        self.context = context
        self.stages_references = stages_references

    def run(self) -> None:
        if self.context.is_clean_required():
            self.logger.info(
                f"Cleaning the whole output directory '{self.context.output_dir}'"
            )
            shutil.rmtree(self.context.output_dir, ignore_errors=True)
        else:
            for stage_reference in self.stages_references:
                self.run_stage(stage_reference)

    def run_stage(self, stage_reference: StageReference) -> None:
        stage_output_dir = self.context.output_dir / stage_reference.group_name
        stage = stage_reference._class(self.context, stage_output_dir)
        stage.output_dir.mkdir(parents=True, exist_ok=True)
        Executor(stage_output_dir).execute(stage)
