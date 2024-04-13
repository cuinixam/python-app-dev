"""Logging utilities."""

import sys
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Generator, Optional, TypeVar

from loguru import logger as _logger
from loguru._logger import Logger

from .docs_utils import fulfills

logger = _logger

# Adding custom logging levels
logger.level("START", no=38, color="<yellow>")
logger.level("STOP", no=39, color="<yellow>")

_R = TypeVar("_R")
_FuncType = Callable[..., _R]


@fulfills("REQ-LOGGING_TIME_IT-0.0.1")
def time_it(message: Optional[str] = None) -> Callable[[_FuncType[_R]], _FuncType[_R]]:
    """Decorator to time a function."""

    def _time_it(func: _FuncType[_R]) -> _FuncType[_R]:
        @wraps(func)
        def time_it(*args: Any, **kwargs: Any) -> _R:
            text = message or f"{func.__module__}.{func.__qualname__}"
            start_time = time.time()
            logger.log("START", f"Starting {text}")
            result = func(*args, **kwargs)
            end_time = time.time()
            logger.log("STOP", f"Finished {text} in {end_time-start_time:.2f}s")
            return result

        return time_it

    return _time_it


@fulfills("REQ-LOGGING_FILE-0.0.1")
def setup_logger(log_file: Optional[Path] = None, clear: bool = True) -> None:
    """Setup logger to stdout and optionally to file."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | <level>{message}</level>",
    )
    if log_file is not None:
        logger.add(log_file, level="DEBUG")
        # Clear log file
        if log_file.exists() and clear:
            log_file.write_text("")


@contextmanager
def log_to_file(
    log_file: Path, my_logger: Optional[Logger] = None, clear: bool = True
) -> Generator[Logger, None, None]:
    used_logger = my_logger if my_logger else logger
    file_handler_id = used_logger.add(log_file)
    # Clear log file
    if log_file.exists() and clear:
        log_file.write_text("")
    try:
        yield used_logger
    finally:
        used_logger.remove(file_handler_id)
