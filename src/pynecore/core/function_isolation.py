from typing import Callable, cast, Any
from types import FunctionType
from collections import defaultdict
from dataclasses import is_dataclass, replace as dataclass_replace
from copy import copy
from .pine_export import Exported

__all__ = ['isolate_function', 'reset', 'reset_step']

# Store all function instances
_function_cache: dict[str, FunctionType] = {}
_call_counters = defaultdict(int)


def reset():
    """
    Reset all function instances and call counters
    """
    _function_cache.clear()
    _call_counters.clear()


def reset_step():
    """
    Reset the call counters for the last bar index
    """
    _call_counters.clear()


def isolate_function(func: FunctionType | Callable, call_id: str | None = None, parent_scope: str = "") -> Callable:
    """
    Create a new function instance with isolated globals if the function has persistent or series globals.

    :param func: The function to create an instance of
    :param call_id: The unique call ID
    :param parent_scope: The parent scope ID
    :return: The new function instance if there are any persistent or series globals otherwise the original function
    """
    # If there is no call ID, return the function as is
    if call_id is None:
        return func

    # Check if this is an Exported proxy and unwrap it
    if isinstance(func, Exported):
        func = func.__fn__
        if func is None:
            raise ValueError("Exported proxy has not been initialized with a function yet")        

    # If it is a type object, return it as is
    if isinstance(func, type):
        return func  # type: ignore
    
    # If it is a classmethod (bound method where __self__ is a class), return it as is
    if hasattr(func, '__self__') and isinstance(func.__self__, type):
        return func

    # If it is an overloaded function, returned by the dispatcher
    is_overloaded = call_id == '__overloaded__?'

    # Create full call ID from parent scope and call ID
    if call_id and not is_overloaded:
        call_id = f"{parent_scope}->{call_id}"

        # Increment counter for this call_id at current bar_index
        _call_counters[call_id] += 1

        # Append the call counter to the call ID
        call_id = f"{call_id}#{_call_counters[call_id]}"

    else:
        call_id = parent_scope

    # If the function is overloaded, we need to remove the dispatcher from the cache to override it with implementation
    if is_overloaded:
        del _function_cache[call_id]

    # The qualified name of the function, this name is used in the globals registry by transformer
    qualname = func.__qualname__.replace('<locals>.', '')

    try:
        # If a function is cached we can just call it
        isolated_function = _function_cache[call_id]

        # We need to create new instance in every run only if the function is inside the main function
        if '.' in qualname:
            # The values may have changed in the original globals
            new_globals = dict(func.__globals__)

            # We need to copy the persistent and series variables from the isolated globals
            old_globals = isolated_function.__globals__
            try:
                for key in new_globals['__persistent_function_vars__'][qualname]:
                    new_globals[key] = old_globals[key]
            except KeyError:
                pass
            try:
                for key in new_globals['__series_function_vars__'][qualname]:
                    new_globals[key] = old_globals[key]
            except KeyError:
                pass
            # Copy the __scope_id__ from the old globals to the new globals to keep scope chain
            new_globals['__scope_id__'] = old_globals['__scope_id__']

            # Create a new function with original closure and isolated globals
            isolated_function = FunctionType(
                func.__code__,
                new_globals,
                func.__name__,
                func.__defaults__,
                func.__closure__
            )
            _function_cache[call_id] = isolated_function

        return isolated_function
    except KeyError:
        pass

    # Builtin objects have no __globals__ attribute
    try:
        new_globals = dict(func.__globals__)
    except AttributeError as e:  # This is a builtin function (it should be filtered in the transformer)
        return func

    # If globals are registered, we can use them
    registry_found = False
    try:
        persistent_vars = new_globals['__persistent_function_vars__']
        registry_found = True
    except KeyError:
        persistent_vars = {}
    try:
        series_vars = new_globals['__series_function_vars__']
        registry_found = True
    except KeyError:
        series_vars = {}

    try:
        for key in persistent_vars[qualname]:
            old_value = new_globals[key]
            if isinstance(old_value, (dict, list)):
                new_globals[key] = old_value.copy()
            elif is_dataclass(old_value):
                new_globals[key] = dataclass_replace(cast(Any, old_value))
            else:
                new_globals[key] = copy(old_value)
    except KeyError:
        pass
    try:
        for key in series_vars[qualname]:
            old_value = new_globals[key]
            new_globals[key] = type(old_value)(old_value._max_bars_back)  # noqa
    except KeyError:
        pass

    # Fallback, if globals are not registered
    if not registry_found:
        # Create new globals with isolated persistent and series
        for key in new_globals.keys():
            if key.startswith('__persistent_') and not key.endswith('_vars__'):
                old_value = new_globals[key]
                if isinstance(old_value, (dict, list)):
                    new_globals[key] = old_value.copy()
                elif is_dataclass(old_value):
                    new_globals[key] = dataclass_replace(cast(Any, old_value))
                else:
                    new_globals[key] = copy(old_value)
            elif key.startswith('__series_') and not key.endswith('_vars__'):
                old_value = new_globals[key]
                new_globals[key] = type(old_value)(old_value._max_bars_back)  # noqa

    new_globals['__scope_id__'] = call_id

    # Create a new function with new closure and globals
    isolated_function = FunctionType(
        func.__code__,
        new_globals,
        func.__name__,
        func.__defaults__,
        func.__closure__
    )

    _function_cache[call_id] = isolated_function
    return isolated_function
