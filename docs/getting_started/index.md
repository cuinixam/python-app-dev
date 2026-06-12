# 🚀 Getting Started

Add the package as a dependency of your project in `pyproject.toml`:

```toml
[project]
dependencies = [
    "py-app-dev",
]
```

Every module shares one logging setup. This is the smallest useful program:

```python
from pathlib import Path

from py_app_dev.core.logging import logger, setup_logger, time_it


@time_it()
def build() -> None:
    logger.info("building ...")


setup_logger(Path("build.log"))  # logs to console and to the file
build()
```

From here, browse the [Features](../features/index.md) for the modules you need.
