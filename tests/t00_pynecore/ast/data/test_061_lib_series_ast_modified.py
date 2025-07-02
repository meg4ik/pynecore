"""
@pyne
"""
from pynecore.core.series import SeriesImpl
from pynecore import lib
from pynecore.core.function_isolation import isolate_function
__series_main·__lib·close__ = SeriesImpl()
__series_main·__lib·low__ = SeriesImpl()
__series_main·a__ = SeriesImpl()
__series_main·c__ = SeriesImpl()
__series_main·nested·__lib·high__ = SeriesImpl()
__series_main·nested·b__ = SeriesImpl()
__series_function_vars__ = {'main': ('__series_main·__lib·close__', '__series_main·__lib·low__', '__series_main·a__', '__series_main·c__'), 'main.nested': ('__series_main·nested·__lib·high__', '__series_main·nested·b__')}
__scope_id__ = ''

def main():
    global __scope_id__
    __lib·close = __series_main·__lib·close__.add(lib.close)
    __lib·low = __series_main·__lib·low__.add(lib.low)
    a = __series_main·a__.add(__series_main·__lib·close__[10])
    print(a)

    def nested():
        __lib·high = __series_main·nested·__lib·high__.add(lib.high)
        b = __series_main·nested·b__.add(__series_main·nested·__lib·high__[1])
        return b
    result = isolate_function(nested, 'main|nested|0', __scope_id__, -1)()
    c = __series_main·c__.add(__series_main·__lib·low__[2])
    print(result, c)
