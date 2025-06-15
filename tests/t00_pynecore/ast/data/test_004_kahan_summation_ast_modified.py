"""
@pyne
"""
__persistent_main·cumulative__ = 0.0
__persistent_main·cumulative___kahan_c__ = 0.0
__persistent_main·counter__ = 0
__persistent_function_vars__ = {'main': ['__persistent_main·cumulative__', '__persistent_main·cumulative___kahan_c__', '__persistent_main·counter__']}

def main():
    global __persistent_main·counter__, __persistent_main·cumulative__, __persistent_main·cumulative___kahan_c__
    ((__kahan_corrected__ := (some_value - __persistent_main·cumulative___kahan_c__)), (__kahan_new_sum__ := (__persistent_main·cumulative__ + __kahan_corrected__)), (__persistent_main·cumulative___kahan_c__ := (__kahan_new_sum__ - __persistent_main·cumulative__ - __kahan_corrected__)), (__persistent_main·cumulative__ := __kahan_new_sum__))[-1]
    __persistent_main·counter__ += 1
