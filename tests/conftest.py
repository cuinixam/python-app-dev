import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def my_python_file(tmp_path: Path) -> Path:
    """Fixture to create a temporary Python file with a sample step."""
    python_file = tmp_path / "my_python_file.py"
    python_file.write_text(
        textwrap.dedent(
            """\
            from typing import List
            from pathlib import Path
            from py_app_dev.core.pipeline import PipelineStep
            class MyStep(PipelineStep):
                def run(self) -> None:
                    pass
                def get_dependencies(self) -> List[Path]:
                    pass
                def get_outputs(self) -> List[Path]:
                    pass
            """
        )
    )
    return python_file
