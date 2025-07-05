"""
@pyne
"""
from pynecore.core.series import SeriesImpl
__series_main·t·s__ = SeriesImpl()
__series_t2·s1__ = SeriesImpl()
__series_t2·s__ = SeriesImpl()
__series_function_vars__ = {'t2': ('__series_t2·s__', '__series_t2·s1__'), 'main.t': ('__series_main·t·s__',)}

def t2(s: float, s1: float):
    s = __series_t2·s__.add(s)
    s1 = __series_t2·s1__.add(s1)
    s = __series_t2·s__.set(s + 1)
    print(s, __series_t2·s__[1], s1, __series_t2·s1__[10])
    return __series_t2·s__[2]

def main():

    def t(s: float):
        s = __series_main·t·s__.add(s)
        s = __series_main·t·s__.set(s + 1)
        print(s, __series_main·t·s__[1])
        return s
    s: float = 1
