"""
@pyne
"""


def main():
    from pynecore.lib import close, ta, hl2
    from pynecore.lib.ta import sma

    print(close, hl2, ta, sma(close, 12))


def __test_import_normalizer_function__(ast_transformed_code, file_reader, log):
    """
    Import normalizer - in function
    """
    try:
        assert ast_transformed_code == file_reader(subdir="data", suffix="_ast_modified.py")
    except AssertionError:
        log.error("AST transformed code:\n%s\n", ast_transformed_code)
        raise
