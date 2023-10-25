import shutil
import subprocess  # nosec
from pathlib import Path
from typing import List, Optional

from .exceptions import UserNotificationException
from .logging import logger


def which(app_name: str) -> Optional[Path]:
    """Return the path to the app if it is in the PATH, otherwise return None."""
    app_path = shutil.which(app_name)
    return Path(app_path) if app_path else None


class SubprocessExecutor:
    def __init__(
        self,
        command: List[str | Path],
        cwd: Optional[Path] = None,
        capture_output: bool = True,
    ):
        self.logger = logger.bind()
        self.command = " ".join([str(cmd) for cmd in command])
        self.current_working_directory = cwd
        self.capture_output = capture_output

    def execute(self) -> None:
        try:
            self.logger.info(f"Running command: {self.command}")
            cwd_path = (self.current_working_directory or Path.cwd()).as_posix()
            with subprocess.Popen(
                self.command.split(),
                cwd=cwd_path,
                stdout=(subprocess.PIPE if self.capture_output else subprocess.DEVNULL),
                stderr=(
                    subprocess.STDOUT if self.capture_output else subprocess.DEVNULL
                ),
                text=True,
            ) as process:  # nosec
                if self.capture_output and process.stdout is not None:
                    for line in iter(process.stdout.readline, ""):
                        self.logger.info(line.strip())
                process.wait()

            # Check return code
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, self.command)
        except subprocess.CalledProcessError as e:
            raise UserNotificationException(
                f"Command '{self.command}' failed with return code {e.returncode}"
            )
        except FileNotFoundError as e:
            raise UserNotificationException(
                f"Command '{self.command}' failed with error {e}"
            )
