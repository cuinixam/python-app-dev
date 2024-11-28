import shutil
import subprocess  # nosec
from pathlib import Path
from typing import Dict, List, Optional, Union

from .exceptions import UserNotificationException
from .logging import logger


def which(app_name: str) -> Optional[Path]:
    """Return the path to the app if it is in the PATH, otherwise return None."""
    app_path = shutil.which(app_name)
    return Path(app_path) if app_path else None


class SubprocessExecutor:
    def __init__(
        self,
        command: Union[str, List[str | Path]],
        cwd: Optional[Path] = None,
        capture_output: bool = True,
        env: Optional[Dict[str, str]] = None,
        shell: bool = False,
    ):
        self.logger = logger.bind()
        self.command = command
        self.current_working_directory = cwd
        self.capture_output = capture_output
        self.env = env
        self.shell = shell

    @property
    def command_str(self) -> str:
        if isinstance(self.command, str):
            return self.command
        return " ".join(str(arg) if not isinstance(arg, str) else arg for arg in self.command)

    def execute(self) -> None:
        try:
            self.logger.info(f"Running command: {self.command_str}")
            cwd_path = (self.current_working_directory or Path.cwd()).as_posix()
            with subprocess.Popen(
                args=self.command,
                cwd=cwd_path,
                stdout=(subprocess.PIPE if self.capture_output else subprocess.DEVNULL),
                stderr=(subprocess.STDOUT if self.capture_output else subprocess.DEVNULL),
                text=True,
                env=self.env,
                shell=self.shell,
            ) as process:  # nosec
                if self.capture_output and process.stdout is not None:
                    for line in iter(process.stdout.readline, ""):
                        self.logger.info(line.strip())
                process.wait()

            # Check return code
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, self.command_str)
        except subprocess.CalledProcessError as e:
            raise UserNotificationException(f"Command '{self.command_str}' failed with return code {e.returncode}") from None
        except FileNotFoundError as e:
            raise UserNotificationException(f"Command '{self.command_str}' failed with error {e}") from None
