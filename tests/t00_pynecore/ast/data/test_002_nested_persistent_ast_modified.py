"""
@pyne
"""
__persistent_main·p__ = 1
__persistent_main·test·p__ = 1
__persistent_function_vars__ = {'main': ('__persistent_main·p__',), 'main.test': ('__persistent_main·test·p__',)}

def main():
    global __persistent_main·p__
    __persistent_main·p__ += 1

    def test():
        global __persistent_main·test·p__
        __persistent_main·test·p__ += 1
        return __persistent_main·test·p__
