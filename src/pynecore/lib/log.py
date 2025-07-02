from typing import Any
import os
import logging

from .string import format as _format
from .. import lib

# Try to import rich, but don't fail if not available
try:
    import rich
    import rich.logging
except ImportError:
    rich = None

__all__ = 'info', 'warning', 'error', 'logger'

if os.environ.get("PYNE_NO_COLOR_LOG", "") == "1":
    rich = None


# noinspection PyProtectedMember
class PineLogFormatter(logging.Formatter):
    """Custom formatter that mimics Pine Script log format"""

    def format(self, record: logging.LogRecord) -> Any:
        """Format log record in Pine style: [timestamp]: message"""
        if record.args:
            msg = _format(record.msg, *record.args)
        else:
            msg = str(record.msg)

        record.args = ()

        record.created = lib._time / 1000
        if rich:
            return msg

        record.msg = msg
        return super().format(record)


# Create logger
logger = logging.getLogger("pyne_core_logger")
# Remove existing handlers before adding new one
if logger.hasHandlers():
    logger.handlers.clear()

logger.setLevel(logging.INFO)
if rich:
    handler = rich.logging.RichHandler(
        show_time=True,  # Disable rich's built-in time handling
        show_level=True,  # Disable rich's built-in level handling
        omit_repeated_times=False,
        markup=False,
        show_path=False,
    )
else:
    handler = logging.StreamHandler()
handler.setFormatter(PineLogFormatter(
    "%(asctime)s %(levelname)-7s %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S%z]")
)
logger.addHandler(handler)


# noinspection PyPep8Naming,PyUnusedLocal
def info(formatString: str, *args: Any, **kwargs: Any) -> None:
    """
    Print an info message to the console.

    :param formatString: Message format string
    :param args: Arguments to format the message
    :param kwargs: Additional arguments (unused)
    """
    logger.info(formatString, *args)


# noinspection PyPep8Naming,PyUnusedLocal
def warning(formatString: str, *args: Any, **kwargs: Any) -> None:
    """
    Print a warning message to the console.

    :param formatString: Message format string
    :param args: Arguments to format the message
    :param kwargs: Additional arguments (unused)
    """
    logger.warning(formatString, *args)


# noinspection PyPep8Naming,PyUnusedLocal
def error(formatString: str, *args: Any, **kwargs: Any) -> None:
    """
    Print an error message to the console.

    :param formatString: Message format string
    :param args: Arguments to format the message
    :param kwargs: Additional arguments (unused)
    """
    logger.error(formatString, *args)
