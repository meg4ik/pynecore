"""
@pyne
"""
from pynecore.core.series import SeriesImpl
from pynecore.core.function_isolation import isolate_function
__series_main·t·a__ = SeriesImpl()
__series_function_vars__ = {'main.t': ('__series_main·t·a__',)}
__scope_id__ = ''

def main():
    global __scope_id__

    def t():
        a = __series_main·t·a__.add(1)
        a = __series_main·t·a__.set(a + 1)
        return __series_main·t·a__[1]
    a = isolate_function(t, 'main|t|0', __scope_id__, -1)()
    print(a)
    b = isolate_function(t, 'main|t|1', __scope_id__, -1)()
    print(b)
