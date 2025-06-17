from copy import copy as _copy
from ..core.class_property import classproperty


class Box:
    _registry = []

    def __init__(self, *_, **kwargs):
        self._registry.append(self)

        self.__dict__.update(**kwargs)

    @classproperty
    def all(cls):  # noqa
        return cls._registry

    @classmethod
    def new(cls, *_, **kwargs):
        return cls(**kwargs)

    def delete(self):
        self.__class__._registry.remove(self)

    # noinspection PyShadowingBuiltins,PyMethodParameters
    def copy(id):
        return _copy(id)

    # noinspection PyMethodMayBeStatic
    def get_top(self, *_, **__):
        from ..lib import high
        return high

    # noinspection PyMethodMayBeStatic
    def get_bottom(self, *_, **__):
        from ..lib import low
        return low

    def set_right(self, *_, **__): ...

    def set_extend(self, *_, **__): ...
