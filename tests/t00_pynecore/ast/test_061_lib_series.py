"""
@pyne
"""
from pynecore import lib
from pynecore import Series


def main():
    a: Series[float] = lib.close[10]
    print(a)
    
    def nested():
        b: Series[float] = lib.high[1]
        return b
    
    result = nested()
    c: Series[float] = lib.low[2]
    print(result, c)


def __test_library_series__(log, ast_transformed_code, file_reader):
    """Library series"""
    try:
        assert ast_transformed_code == file_reader(subdir="data", suffix="_ast_modified.py")
    except AssertionError:
        log.error("AST transformed code:\n%s\n", ast_transformed_code)
        raise
