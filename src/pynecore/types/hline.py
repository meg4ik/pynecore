from typing import Any
from .base import IntEnum


class _HLineEnum(IntEnum):
    ...


class HLineConstants:
    style_solid = _HLineEnum()
    style_dotted = _HLineEnum()
    style_dashed = _HLineEnum()


class HLine(HLineConstants):

    def __init__(self, price: Any, title: str | None = None, color: Any = None,
                 linestyle: Any = None, linewidth: int = 1, *_, **__):
        """
        Draw a horizontal line at a fixed price level

        :param price: The price level at which the line will be drawn
        :param title: The title of the line
        :param color: The color of the line
        :param linestyle: The style of the line
        :param linewidth: The width of the line
        :return: A HLine object
        """
