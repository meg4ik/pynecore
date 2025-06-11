"""
Builtin library of Pyne
"""
from typing import TypeAlias, Any, Callable

import sys

from functools import lru_cache
from datetime import datetime, UTC

from pynecore.types.source import Source

from ..core.module_property import module_property
from ..core.script import script, input

from ..types.series import Series
from ..types.na import NA
from ..types.plot import Plot
from ..types.hline import HLine
from ..types.alert import Alert
from . import plot_style as _plot_style
from . import hline_style as _hline_style
from . import alert as _alert

from . import syminfo  # This should be imported before core.datetime to avoid circular import!
from . import barstate, string, log, math

from pynecore.core.overload import overload
from pynecore.core.datetime import parse_datestring as _parse_datestring, parse_timezone as _parse_timezone

__all__ = [
    # Other modules
    'syminfo', 'barstate', 'string', 'log', 'math',

    # Variables
    'bar_index',
    'open', 'high', 'low', 'close', 'volume',
    'hl2', 'hlc3', 'ohlc4', 'hlcc4',

    # Functions / objects
    'input', 'script',

    'timestamp',

    'plot', 'plotchar', 'plotarrow', 'plotbar', 'plotcandle', 'plotshape', 'barcolor', 'bgcolor',
    'fill', 'hline',

    'alert', 'alertcondition',

    'fixnan', 'nz',

    # Module properties
    'dayofmonth', 'dayofweek', 'hour', 'minute', 'month', 'second', 'weekofyear', 'year',
    'time', 'na',
]

#
# Constants
#

# For better type hints
TimezoneStr: TypeAlias = str  # e.g. "UTC-5", "GMT+0530", "America/New_York"
DateStr: TypeAlias = str  # e.g. "2020-02-20", "20 Feb 2020"

#
# Module variables
#

bar_index: Series[int] = 0

open: Series[float] | NA[float] = Source("open")  # noqa (shadowing built-in name (open) intentionally)
high: Series[float] | NA[float] = Source("high")
low: Series[float] | NA[float] = Source("low")
close: Series[float] | NA[float] = Source("close")
volume: Series[float] | NA[float] = Source("volume")

hl2: Series[float] | NA[float] = Source("hl2")
hlc3: Series[float] | NA[float] = Source("hlc3")
ohlc4: Series[float] | NA[float] = Source("ohlc4")
hlcc4: Series[float] | NA[float] = Source("hlcc4")

# Store time as integer as in Pine Scripts timestamp format
_time: int = 0
# Datetime object in the exchange timezone
_datetime: datetime = datetime.fromtimestamp(0, UTC)

# Script settings from `script.indicator`, `script.strategy` or `script.library`
_script: script | None = None

# Stores data to polot
_plot_data: dict[str, Any] = {}

# Lib semaphore - to prevent lib`s main function to do things it must not (plot, strategy things, etc.)
_lib_semaphore = False


#
# Functions
#

### Date / Time ###

# noinspection PyShadowingNames
def _get_dt(time: int | None = None, timezone: str | None = None) -> datetime:
    """ Get datetime object from time and timezone """
    dt = _datetime if time is None else datetime.fromtimestamp(time / 1000, UTC)
    assert dt is not None
    return dt.astimezone(_parse_timezone(timezone))


@lru_cache(maxsize=1024)
@overload
def timestamp(date_string: DateStr) -> int:  # type: ignore  # It is more pythonic, but not supported by Pine Script
    """
    Parse date string and return UNIX timestamp in milliseconds

    Multiple calling formats supported:
    - timestamp("2020-02-20T15:30:00+02:00")  # ISO 8601
    - timestamp("20 Feb 2020 15:30:00 GMT+0200")  # RFC 2822
    - timestamp("Feb 01 2020 22:10:05")       # Pine format
    - timestamp("2011-10-10T14:48:00")        # Pine format without timezone

    :param date_string: Date string in Pine Script format
    :return: UNIX timestamp in milliseconds
    """
    dt = _parse_datestring(date_string)
    return int(dt.timestamp() * 1000)


# noinspection PyPep8Naming
@overload
def timestamp(dateString: DateStr) -> int:  # type: ignore
    """
    Parse date string and return UNIX timestamp in milliseconds

    Multiple calling formats supported:
    - timestamp("2020-02-20T15:30:00+02:00")  # ISO 8601
    - timestamp("20 Feb 2020 15:30:00 GMT+0200")  # RFC 2822
    - timestamp("Feb 01 2020 22:10:05")       # Pine format
    - timestamp("2011-10-10T14:48:00")        # Pine format without timezone
    - timestamp("UTC-5", 2020, 2, 20, 15, 30) # With timezone

    :param dateString: Date string in Pine Script format
    :return: UNIX timestamp in milliseconds
    """
    return timestamp(date_string=dateString)


# noinspection PyShadowingNames
@overload
def timestamp(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> int:  # type: ignore
    """
    Create timestamp from date/time components:
    - timestamp(2020, 2, 20, 15, 30)          # From components
    - timestamp(2020, 2, 20, 15, 30, 0)       # With seconds

    :param year: Year
    :param month: Month
    :param day: Day
    :param hour: Hour
    :param minute: Minute
    :param second: Second
    :return: UNIX timestamp in milliseconds
    """
    return timestamp(None, year=year, month=month, day=day, hour=hour, minute=minute, second=second)


# noinspection PyShadowingNames
@overload
def timestamp(timezone: TimezoneStr | None, year: int, month: int, day: int,
              hour: int = 0, minute: int = 0, second: int = 0) -> int:
    """
    Create timestamp from date/time components with timezone:
    - timestamp("UTC-5", 2020, 2, 20, 15, 30)
    - timestamp("GMT+0530", 2020, 2, 20, 15, 30)

    :param timezone: Timezone string
    :param year: Year
    :param month: Month
    :param day: Day
    :param hour: Hour
    :param minute: Minute
    :param second: Second
    :return: UNIX timestamp in milliseconds
    """
    tz = _parse_timezone(timezone)
    dt = datetime(year, month, day, hour, minute, second, tzinfo=tz)
    return int(dt.timestamp() * 1000)


### Plotting ###

# TODO: implement creating plot metadata to be able to plot in a different module

def barcolor(*_, **__):
    ...


def bgcolor(*_, **__):
    ...


def fill(*_, **__):
    ...


class _HLine:
    # Shortcuts to hline styles for Pine Script compatibility
    style_solid = _hline_style.style_solid
    style_dotted = _hline_style.style_dotted
    style_dashed = _hline_style.style_dashed

    def __call__(self, price: Any, title: str | None = None, color: Any = None,
                 linestyle: Any = None, linewidth: int = 1, *_, **__) -> HLine:
        """
        Draw a horizontal line at a fixed price level

        :param price: The price level at which the line will be drawn
        :param title: The title of the line
        :param color: The color of the line
        :param linestyle: The style of the line
        :param linewidth: The width of the line
        :return: A HLine object
        """
        return HLine()


# Create an instance of _HLine to be used as both a function and a module
hline = _HLine()


class _Plot:
    # Shortcuts to plot styles for Pine Script compatibility
    style_area = _plot_style.style_area
    style_areabr = _plot_style.style_areabr
    style_circles = _plot_style.style_circles
    style_columns = _plot_style.style_columns
    style_cross = _plot_style.style_cross
    style_histogram = _plot_style.style_histogram
    style_line = _plot_style.style_line
    style_linebr = _plot_style.style_linebr
    style_stepline = _plot_style.style_stepline
    style_stepline_diamond = _plot_style.style_stepline_diamond

    def __call__(self, series: Any, title: str | None = None, *_, **__) -> Plot:
        """
        Plot series, by default a CSV is generated, but this can be extended

        :param series: The value to plot in every bar
        :param title: The title of the plot, if multiple plots are created with the same title, a
                      number will be appended
        :return: The a Plot object, can be used to reference the plot in other functions
        """
        if _lib_semaphore:
            return Plot(title)

        if bar_index == 0:  # Only check if it is the first bar for performance reasons
            # Check if it is called from the main function
            if sys._getframe(1).f_code.co_name != 'main':  # noqa
                raise RuntimeError("The plot function can only be called from the main function!")

        # Ensure unique title
        if title is None:
            title = 'Plot'
        if title in _plot_data:
            c = 0
            t = title
            while t in _plot_data:
                t = title + ' ' + str(c)
                c += 1
            title = t

        # Store plot data
        _plot_data[title] = series

        return Plot(title)


plot = _Plot()


def plotarrow(*_, **__):
    ...


def plotbar(*_, **__):
    ...


def plotcandle(*_, **__):
    ...


def plotchar(series: Any, title: str | None = None, *_, **__):
    plot(series, title)


def plotshape(*_, **__):
    ...


### Alert ###

# noinspection PyUnusedLocal
def alert(message: str, freq: Alert = _alert.freq_once_per_bar):
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


def alertcondition(*_, **__):
    """
    Define alert condition. Currently implemented as no-op.

    In the future this could be used to define alert conditions
    that can be triggered based on boolean expressions.
    """
    if bar_index == 0:  # Only check if it is the first bar for performance reasons
        # Check if it is called from the main function
        if sys._getframe(1).f_code.co_name != 'main':  # noqa
            raise RuntimeError("The alertcondition function can only be called from the main function!")


### Other ###

__persistent_last_not_nan__: Any = NA(None)
__persistent_function_vars__ = {'fixnan': ['__persistent_last_not_nan__']}


def fixnan(source: Any) -> Any:
    """
    Fix NA values by replacing them with the last non-NA value

    :param source: The source value
    :return: The source value if it is not NA, otherwise the last non-NA value
    """
    global __persistent_last_not_nan__
    __persistent_last_not_nan__ = source if not isinstance(source, NA) else __persistent_last_not_nan__
    return __persistent_last_not_nan__


def is_na(source: Any = None) -> bool | NA:
    """
    Check if the source is NA
    """
    if source is None:
        return NA(None)
    # If the source is a type, return NA of that type
    if isinstance(source, type) and source is not NA:
        return NA(source)
    return isinstance(source, NA) or source is NA


# In Pine Script, na is both a property and a function
na: Callable[[Any], bool | NA] | Any = is_na


def nz(source: Any, replacement: Any = 0) -> Any:
    """
    Replace NA values with a replacement value or 0 if not specified

    :param source: The source value
    :param replacement: The replacement value, default is 0
    :return: The source value if it is not NA, otherwise the replacement value
    """
    if isinstance(source, NA):
        return replacement
    return source


#
# Module properties
#

### Date / Time ###

# noinspection PyShadowingNames
@module_property
def dayofmonth(time: int | None = None, timezone: str | None = None) -> int:
    """
    Day of the month

    :param time: The time to get the day of the month from, if None the current time is used
    :param timezone: The timezone of the time, if not specified the exchange timezone is used
    :return: The day of the month
    """
    return _get_dt(time, timezone).day


# noinspection PyShadowingNames
@module_property
def dayofweek(time: int | None = None, timezone: str | None = None) -> int:
    """
    Day of the week

    :param time: The time to get the day of the week from, if None the current time is used
    :param timezone: The timezone of the time, if not specified the exchange timezone is used
    :return: The day of the week, 1 is Sunday, 2 is Monday, ..., 7 is Saturday
    """
    res = _get_dt(time, timezone).weekday() + 2
    if res == 8:
        res = 1
    return res


# noinspection PyShadowingNames
@module_property
def hour(time: int | None = None, timezone: str | None = None) -> int:
    """
    Hour of the day

    :param time: The time to get the hour of the day from, if None the current time is used
    :param timezone: The timezone of the time, if not specified the exchange timezone is used
    :return: The hour of the day
    """
    return _get_dt(time, timezone).hour


# noinspection PyShadowingNames
@module_property
def minute(time: int | None = None, timezone: str | None = None) -> int:
    """
    Minute of the hour

    :param time: The time to get the minute of the hour from, if None the current time is used
    :param timezone: The timezone of the time, if not specified the exchange timezone is used
    :return: The minute of the hour
    """
    return _get_dt(time, timezone).minute


# noinspection PyShadowingNames
@module_property
def month(time: int | None = None, timezone: str | None = None) -> int:
    """
    Month of the year

    :param time: The time to get the month of the year from, if None the current time is used
    :param timezone: The timezone of the time, if not specified the exchange timezone is used
    :return: The month of the year
    """
    return _get_dt(time, timezone).month


# noinspection PyShadowingNames
@module_property
def second(time: int | None = None, timezone: str | None = None) -> int:
    """
    Second of the minute

    :param time: The time to get the second of the minute from, if None the current time is used
    :param timezone: The timezone of the time, if not specified the exchange timezone is used
    :return: The second of the minute
    """
    return _get_dt(time, timezone).second


@module_property
def time(timeframe: str | None = None, *_, **__) -> int:
    if timeframe is None:
        return _time
    raise NotImplementedError("The time() function is not fully implemented yet!")
    # TODO: Implement time function


# noinspection PyShadowingNames
@module_property
def weekofyear(time: int | None = None, timezone: str | None = None) -> int:
    """
    Week of the year

    :param time: The time to get the week of the year from, if None the current time is used
    :param timezone: The timezone of the time, if not specified the exchange timezone is used
    :return: The week of the year
    """
    return _get_dt(time, timezone).isocalendar()[1]


# noinspection PyShadowingNames
@module_property
def year(time: int | None = None, timezone: str | None = None) -> int:
    """
    Year

    :param time: The time to get the year from, if None the current time is used
    :param timezone: The timezone of the time, if not specified the exchange timezone is used
    :return: The year
    """
    return _get_dt(time, timezone).year
