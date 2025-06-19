from typing import Any, Callable
from ..lib import array, matrix, box, line
from ..types.matrix import Matrix

from .function_isolation import isolate_function

__scope_id__ = ''


def method(func: Callable) -> Callable:
    """
    Decorator to mark a function as a Pine method.
    This is used to indicate that the function should be treated as a method in Pine Script.
    """
    setattr(func, '__pine_method__', True)
    return func


def _get_builtin_method(method_name: str, var: Any) -> Callable | None:
    """
    Get the built-in method for a Pine Script object.
    :param method_name: The name of the method
    :param var: The object on which the method is being called
    :return: The built-in method, or None if not found
    """
    try:
        if isinstance(var, list):
            return getattr(array, method_name)

        elif isinstance(var, Matrix):
            return getattr(matrix, method_name)

        elif isinstance(var, line.Line):
            return getattr(line, method_name)

        elif isinstance(var, box.Box):
            return getattr(box, method_name)
    except AttributeError:
        pass

    return None


# noinspection PyShadowingNames
def method_call(method: str | Callable, var: Any, *args, **kwargs) -> Any:
    """
    Dispatch a method call on a Pine Script variable to the appropriate handler.

    This function serves as the central dispatcher for Pine Script method calls, handling both
    built-in type methods (like array and matrix operations) and user-defined local methods.
    It provides the Pine Script-like method calling syntax by routing calls to the correct
    implementation based on the variable type and method name.

    :param method: The method to call, either as a string name (for built-in methods) or a callable (for local methods)
    :param var: The object/variable on which the method is being called (e.g., array, matrix, or custom object)
    :param args: Positional arguments to pass to the method
    :param kwargs: Keyword arguments to pass to the method
    :return: The result of the method call, or None if the method cannot be dispatched
    :raises AssertionError: If a string method name is provided but no matching method is found for the variable type
    """
    global __scope_id__

    # If method is a string
    if isinstance(method, str):
        # Support for builtin methods
        _method = _get_builtin_method(method, var)
        if _method is not None:
            return _method(var, *args, **kwargs)

        # Modules
        try:
            return getattr(var, method)(*args, **kwargs)
        except AttributeError:
            pass

        assert False, f'No such method: {var}->{method}'

    # It is a local method, it should be a local function
    elif callable(method):
        # It may not detected well the type and there may be a user with the same method name.
        # So we 1st trt if it is a built-in object and has that method, because it has priority
        _method = _get_builtin_method(method.__name__, var)
        if _method:
            return _method(var, *args, **kwargs)

        return isolate_function(method, '__method_call__', __scope_id__)(var, *args, **kwargs)

    return None
