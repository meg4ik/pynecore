"""
@pyne
"""
from pynecore import lib
import pynecore.lib.ta
from pynecore.core.function_isolation import isolate_function
__scope_id__ = ''

def main():
    global __scope_id__
    print(lib.close, lib.hl2, lib.ta, isolate_function(lib.ta.sma, 'main|lib.ta.sma|0', __scope_id__)(lib.close, 12))
