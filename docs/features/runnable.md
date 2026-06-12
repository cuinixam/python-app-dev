# Handle Task Execution

To optimize an application, you want to avoid executing tasks with high computational cost if they are not necessary.
A simple way to avoid unnecessary executions is to check whether the inputs and outputs of a task have changed since the last execution.
If there are no changes, the task is skipped, saving time and resources.

## Usage

Subclass `Runnable`, declare the task's inputs and outputs, then hand it to an `Executor`. The executor skips the task when nothing changed since the last run:

```python
from pathlib import Path

from py_app_dev.core.runnable import Executor, Runnable


class GenerateReport(Runnable):
    def __init__(self, source: Path, report: Path) -> None:
        super().__init__()
        self.source = source
        self.report = report

    def get_name(self) -> str:
        return "generate_report"

    def run(self) -> int:
        self.report.write_text(self.source.read_text().upper())
        return 0

    def get_inputs(self) -> list[Path]:
        return [self.source]

    def get_outputs(self) -> list[Path]:
        return [self.report]


executor = Executor(cache_dir=Path(".cache"))
executor.execute(GenerateReport(Path("in.txt"), Path("out.txt")))  # runs
executor.execute(GenerateReport(Path("in.txt"), Path("out.txt")))  # skipped, nothing changed
```

Pass `force_run=True` to `Executor` to run even when nothing changed, or `dry_run=True` to report what would run without touching the system.

## Requirements

```{item} REQ-RUNNABLE-0.0.1 Executing a New Task

   Execute a new task to ensure it runs even in the absence of previous execution data.
```

```{item} REQ-RUNNABLE-0.0.2 Skipping Execution

   Skip the execution of a task if its inputs and outputs have not changed since the last execution to save time and resources.
```

```{item} REQ-RUNNABLE-0.0.3 Force Execution

   Force the execution of a task, even if dependencies haven't changed, to accommodate tasks that might produce different outputs under identical input conditions.
```

```{item} REQ-RUNNABLE-0.0.4 Dry Run Execution

   Perform a dry run, simulating the execution of tasks without actual running, to enable testing and debugging of the execution sequence without affecting the system state.
```

```{item} REQ-RUNNABLE-0.0.5 Handling Input and Output Changes

   Re-execute a task if any of its input or output files have changed, been added, or been removed to ensure that tasks are performed based on the most current data conditions.
```

```{item} REQ-RUNNABLE-0.0.6 Caching Execution Metadata

   The system uses a caching mechanism to store execution metadata (file hashes) to optimize performance and avoid unnecessary re-executions.
```
