"""
@pyne
"""
from pynecore import lib
from pynecore.lib import box


def main():
    def nested():
        # Test library series indexing in conditional expression
        value = lib.low[1] if True else lib.low
        
        # Test in function call argument with conditional
        my_box: box = box(lib.high[2] if False else lib.high)
        
        # Test nested conditional with indexing
        result = lib.close[3] if lib.open[1] > 100 else lib.close
        
        return value, my_box, result
    
    res = nested()
    print(res)


def __test_library_series_conditional__(log, ast_transformed_code, file_reader):
    """Library series in conditional expressions"""
    try:
        assert ast_transformed_code == file_reader(subdir="data", suffix="_ast_modified.py")
    except AssertionError:
        log.error("AST transformed code:\n%s\n", ast_transformed_code)
        raise