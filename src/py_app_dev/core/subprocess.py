import contextlib
import locale
import queue
import shutil
import subprocess  # nosec
import threading
import time
from pathlib import Path
from typing import Any

import psutil

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
        timeout: Maximum runtime in seconds before the subprocess is forcefully terminated. If None, there is no timeout.

    """

    def __init__(
        self,
        command: str | list[str | Path],
        cwd: Path | None = None,
        capture_output: bool = True,
        env: dict[str, str] | None = None,
        shell: bool = False,
        print_output: bool = True,
        timeout: int | None = None,
    ):
        self.logger = logger.bind()
        self.command = command
        self.current_working_directory = cwd
        self.capture_output = capture_output
        self.env = env
        self.shell = shell
        self.print_output = print_output
        self.timeout = timeout

    @property
    def command_str(self) -> str:
        if isinstance(self.command, str):
            return self.command
        return " ".join(str(arg) if not isinstance(arg, str) else arg for arg in self.command)

    def _finalize_process(
        self,
        process: subprocess.Popen[Any] | None,
    ) -> None:
        """
        Clean up a subprocess and its children.

        If the process is still running it is forcibly killed (children first,
        then parent).  This is a no-op when the process has already finished.
        """
        if process is None:
            return
        wait_timeout_seconds: float = 5.0
        try:
            if process.poll() is None:
                try:
                    parent = psutil.Process(process.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    parent = None

                if parent:
                    for child in parent.children(recursive=True):
                        with contextlib.suppress(Exception):
                            child.kill()
                    with contextlib.suppress(Exception):
                        parent.kill()
        except Exception as exc:
            self.logger.error(f"Failed to kill process tree for PID {getattr(process, 'pid', 'unknown')}: {exc}")

        with contextlib.suppress(BaseException):
            process.wait(timeout=wait_timeout_seconds)

        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe:
                with contextlib.suppress(Exception):
                    pipe.close()

    def execute(self, handle_errors: bool = True) -> subprocess.CompletedProcess[Any] | None:
        """Execute the command and return the CompletedProcess object if handle_errors is False."""
        start_time = time.monotonic()
        completed_process: subprocess.CompletedProcess[Any] | None = None
        stdout = ""
        stderr = ""
        self.logger.info(f"Running command: {self.command_str}")
        cwd_path = (self.current_working_directory or Path.cwd()).as_posix()
        process: subprocess.Popen[str] | None = None
        streaming_active = False

        try:
            process = subprocess.Popen(
                args=self.command,
                cwd=cwd_path,
                # Combine both streams to stdout (when captured)
                stdout=(subprocess.PIPE if self.capture_output else subprocess.DEVNULL),
                stderr=(subprocess.STDOUT if self.capture_output else subprocess.DEVNULL),
                bufsize=1,  # line buffering, flushed after each \n
                text=True,
                universal_newlines=True,  # normalize line endings to \n
                encoding=locale.getpreferredencoding(False),
                errors="replace",  # replace undecodable bytes with �
                env=self.env,
                shell=self.shell,
            )
            # STREAMING OUTPUT MODE
            if self.capture_output and self.print_output and process.stdout is not None:
                # Drain stdout on a background thread so the main loop is never
                # blocked by readline() when the process is silent.  A sentinel
                # None is pushed after EOF so the consumer knows when to stop.
                streaming_active = True
                line_queue: queue.Queue[str | None] = queue.Queue()

                def _reader(src: Any, dest: queue.Queue[str | None]) -> None:
                    for ln in src:
                        dest.put(ln)
                    dest.put(None)

                reader_thread = threading.Thread(target=_reader, args=(process.stdout, line_queue), daemon=True)
                reader_thread.start()

                while True:
                    # Timeout check runs even when the process writes nothing
                    if self.timeout is not None and (time.monotonic() - start_time) > self.timeout:
                        raise subprocess.TimeoutExpired(
                            cmd=self.command_str,
                            timeout=self.timeout,
                            output=stdout,
                        )
                    try:
                        line = line_queue.get(timeout=0.05)
                    except queue.Empty:
                        continue
                    if line is None:  # EOF sentinel
                        break
                    self.logger.info(line.strip())
                    stdout += line

                reader_thread.join()
                process.wait()
            # NON-STREAMING MODE
            elif self.capture_output and not self.print_output:
                stdout, stderr = process.communicate(timeout=self.timeout)
            else:
                # No output capturing; just wait for completion
                process.wait(timeout=self.timeout)

            if handle_errors:
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, self.command_str, stdout, stderr)
            else:
                completed_process = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
        except subprocess.TimeoutExpired:
            raise UserNotificationException(f"Command '{self.command_str}' timed out after {self.timeout} seconds and was forcefully terminated.") from None
        except subprocess.CalledProcessError as e:
            raise UserNotificationException(f"Command '{self.command_str}' execution failed with return code {e.returncode}") from None
        except FileNotFoundError as e:
            raise UserNotificationException(f"Command '{self.command_str}' could not be executed. Failed with error {e}") from None
        except KeyboardInterrupt:
            raise UserNotificationException(f"Command '{self.command_str}' execution interrupted by user") from None
        finally:
            # Kill the process first so pipe EOF unblocks the reader thread
            self._finalize_process(process=process)
            if streaming_active:
                with contextlib.suppress(Exception):
                    reader_thread.join(timeout=2.0)
        return completed_process
