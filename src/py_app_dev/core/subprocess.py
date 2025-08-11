import locale
import shutil
import subprocess  # nosec
from pathlib import Path
from typing import Any

from .exceptions import UserNotificationException
from .logging import logger


def which(app_name: str) -> Path | None:
    """Return the path to the app if it is in the PATH, otherwise return None."""
    app_path = shutil.which(app_name)
    return Path(app_path) if app_path else None


class SubprocessExecutor:
    """
    Execute a command in a subprocess.

    Args:
    ----
        capture_output: If True, the output of the command will be captured.
        print_output: If True, the output of the command will be printed to the logger.
                      One can set this to false in order to get the output in the returned CompletedProcess object.

    """

    def __init__(
        self,
        command: str | list[str | Path],
        cwd: Path | None = None,
        capture_output: bool = True,
        env: dict[str, str] | None = None,
        shell: bool = False,
        print_output: bool = True,
    ):
        self.logger = logger.bind()
        self.command = command
        self.current_working_directory = cwd
        self.capture_output = capture_output
        self.env = env
        self.shell = shell
        self.print_output = print_output

    @property
    def command_str(self) -> str:
        if isinstance(self.command, str):
            return self.command
        return " ".join(str(arg) if not isinstance(arg, str) else arg for arg in self.command)

    def execute(self, handle_errors: bool = True) -> subprocess.CompletedProcess[Any] | None:
        """Execute the command and return the CompletedProcess object if handle_errors is False."""
        try:
            completed_process = None
            stdout = ""
            stderr = ""
            self.logger.info(f"Running command: {self.command_str}")
            cwd_path = (self.current_working_directory or Path.cwd()).as_posix()
            with subprocess.Popen(
                args=self.command,
                cwd=cwd_path,
                # Combine both streams to stdout (when captured)
                stdout=(subprocess.PIPE if self.capture_output else subprocess.DEVNULL),
                stderr=(subprocess.STDOUT if self.capture_output else subprocess.DEVNULL),
                # enables line buffering, line is flushed after each \n
                bufsize=1,
                text=True,
                # every new line is a \n
                universal_newlines=True,
                # decode bytes to str using current locale/system encoding
                encoding=locale.getpreferredencoding(False),
                # replace unknown characters with �
                errors="replace",
                env=self.env,
                shell=self.shell,
            ) as process:  # nosec
                if self.capture_output and process.stdout is not None:
                    if self.print_output:
                        for line in iter(process.stdout.readline, ""):
                            self.logger.info(line.strip())
                            stdout += line
                        process.wait()
                    else:
                        stdout, stderr = process.communicate()

            if handle_errors:
                # Check return code
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, self.command_str)
            else:
                completed_process = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
        except subprocess.CalledProcessError as e:
            raise UserNotificationException(f"Command '{self.command_str}' execution failed with return code {e.returncode}") from None
        except FileNotFoundError as e:
            raise UserNotificationException(f"Command '{self.command_str}' could not be executed. Failed with error {e}") from None
        except KeyboardInterrupt:
            raise UserNotificationException(f"Command '{self.command_str}' execution interrupted by user") from None
        return completed_process
