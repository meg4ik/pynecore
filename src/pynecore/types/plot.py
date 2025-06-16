from typing import Any
import sys
from .base import IntEnum


class _PlotEnum(IntEnum):
    ...


class PlotConstants:
    style_area = _PlotEnum()
    style_areabr = _PlotEnum()
    style_circles = _PlotEnum()
    style_columns = _PlotEnum()
    style_cross = _PlotEnum()
    style_histogram = _PlotEnum()
    style_line = _PlotEnum()
    style_linebr = _PlotEnum()
    style_stepline = _PlotEnum()
    style_stepline_diamond = _PlotEnum()


# noinspection PyProtectedMember
class Plot(PlotConstants):

    def __init__(self, series: Any, title: str | None = None, *_, **__):
        """
        Plot series, by default a CSV is generated, but this can be extended

        :param series: The value to plot in every bar
        :param title: The title of the plot, if multiple plots are created with the same title, a
                      number will be appended
        :return: The a Plot object, can be used to reference the plot in other functions
        """
        from .. import lib
        if lib._lib_semaphore:
            return

        if lib.bar_index == 0:  # Only check if it is the first bar for performance reasons
            # Check if it is called from the main function
            if sys._getframe(1).f_code.co_name != 'main':  # noqa
                raise RuntimeError("The plot function can only be called from the main function!")

        # Ensure unique title
        if title is None:
            title = 'Plot'
        if title in lib._plot_data:
            c = 0
            t = title
            while t in lib._plot_data:
                t = title + ' ' + str(c)
                c += 1
            title = t

        # Store plot data
        lib._plot_data[title] = series
