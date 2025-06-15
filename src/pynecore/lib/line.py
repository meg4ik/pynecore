from copy import copy as _copy

from ..types.line import Line

from ..core.module_property import module_property


def new(*args, **kwargs):
    return Line()


# noinspection PyShadowingBuiltins
def copy(id):
    return _copy(id)


# noinspection PyShadowingBuiltins
@module_property
def all():
    return []
