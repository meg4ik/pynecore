from __future__ import annotations
from ..types.base import IntEnum


class _AlertEnum(IntEnum):
    ...


class AlertConstants:
    freq_all = _AlertEnum()
    freq_once_per_bar = _AlertEnum()
    freq_once_per_bar_close = _AlertEnum()


class Alert(AlertConstants):

    # noinspection PyUnusedLocal
    def __init__(self, message: str, freq: AlertConstants = AlertConstants.freq_once_per_bar):
        """
        Display alert message. Uses rich formatting if available, falls back to print.

        :param message: Alert message to display
        :param freq: Alert frequency (currently ignored)
        """
        try:
            # Try to use typer for nice colored output
            import typer
            typer.secho(f"🚨 ALERT: {message}", fg=typer.colors.BRIGHT_YELLOW, bold=True)
        except ImportError:
            # Fallback to simple print
            print(f"🚨 ALERT: {message}")
