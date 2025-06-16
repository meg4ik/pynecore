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

    @classmethod
    def delete(cls):
        cls._registry.remove(cls)

    # noinspection PyShadowingBuiltins,PyMethodParameters
    def copy(id):
        return _copy(id)
