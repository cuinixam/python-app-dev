import textwrap
from pathlib import Path
from typing import List

import pytest

from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.pipeline import PipelineLoader, Stage, StageConfig


def test_load_unknown_stage():
    with pytest.raises(UserNotificationException):
        PipelineLoader._load_stages(
            "install", [StageConfig(stage="StageIDontExist")], Path(".")
        )


def test_load_stage_from_file(tmp_path: Path) -> None:
    my_python_file = tmp_path / "my_python_file.py"
    my_python_file.write_text(
        textwrap.dedent(
            """\
            from typing import List
            from pathlib import Path
            from py_app_dev.core.pipeline import Stage
            class MyStage(Stage):
                def run(self) -> None:
                    pass
                def get_dependencies(self) -> List[Path]:
                    pass
                def get_outputs(self) -> List[Path]:
                    pass
            """
        )
    )
    result = PipelineLoader._load_stages(
        "install", [StageConfig(stage="MyStage", file="my_python_file.py")], tmp_path
    )
    assert len(result) == 1
    assert result[0].group_name == "install"
    assert result[0]._class.__name__ == "MyStage"


class MyTestStage(Stage):
    def run(self) -> int:
        return 0

    def get_dependencies(self) -> List[Path]:
        return []

    def get_outputs(self) -> List[Path]:
        return []


def test_load_module_stage_builtin():
    module_name = "tests.test_pipeline"
    stage_class_name = "MyTestStage"
    result = PipelineLoader._load_module_stage(module_name, stage_class_name)
    assert result == MyTestStage
