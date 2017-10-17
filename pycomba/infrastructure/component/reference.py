# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        reference
# Purpose:     References to components or members of components
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2017 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""References to components or members of components"""


# standard library imports
from abc import ABCMeta
from typing import Any, Dict, Optional, Text, Tuple, Type
from weakref import ref as WeakRef

# third-party imports


# local imports
from . import Component, Immutable, UniqueIdentifier
from .attribute import AbstractAttribute


class ReferenceMeta(ABCMeta):

    """Metaclass for class `Reference`."""

    def __new__(mcls: Type, name: str, bases: Tuple[Type, ...],
                namespace: Dict, ref_type: Optional[Type[Component]] = None) \
            -> Type:
        assert ref_type is None or issubclass(ref_type, Component), ref_type
        new_cls = super().__new__(mcls, name, bases, namespace)
        new_cls._ref_type = ref_type
        return new_cls

    @property
    def ref_type(cls) -> Optional[Type[Component]]:
        return cls._ref_type

    @property
    def __origin__(cls):
        if cls.ref_type is None:
            return cls
        return cls.__bases__[1]

    def __getitem__(cls, ref_type: Type[Component]):
        assert issubclass(ref_type, Component), ref_type
        namespace = dict(cls.__dict__)
        # remove slots
        try:
            slots = namespace['__slots__']
        except KeyError:
            pass
        else:
            for name in slots:
                namespace.pop(name, None)
        return type(cls)(cls.__name__,
                         (cls,) + cls.__bases__,
                         namespace,
                         ref_type=ref_type)

    def __subclasscheck__(cls, subcls: type) -> bool:
        # issubclass(Refrerence[T1], Reference[T2]) == issubclass(T1, T2)
        if cls.__origin__ in subcls.__mro__:
            return cls.ref_type is None or (subcls.ref_type is not None and
                                            issubclass(subcls.ref_type,
                                                       cls.ref_type))
        return False

    def __repr__(cls):
        """repr(cls)"""
        if cls.ref_type is None:
            return f"{cls.__module__}.{cls.__qualname__}"
        else:
            return f"{cls.__module__}.{cls.__qualname__}[{cls.ref_type!r}]"


class Reference(AbstractAttribute, metaclass=ReferenceMeta):

    """Descriptor class for defining attributes of objects holding
    references to components."""

    __isabstractmethod__ = False

    def __init__(self, immutable: bool = False,
                 doc: Optional[Text] = None) -> None:
        if self.ref_type is None:
            raise TypeError(
                f"Class '{self.__class__.__qualname__}' cannot be "
                "instantiated.")
        super().__init__(immutable=immutable, doc=doc)

    @property
    def ref_type(self) -> Optional[Type[Component]]:
        return self.__class__.ref_type

    def __get__(self, instance: Any, owner: type) -> Component:
        """Return referenced object."""
        if instance is None:    # if accessed via class, return descriptor
            return self         # (i.e. self),
        else:                   # else return referenced object
            try:
                (uid, ref) = getattr(instance, self._priv_member)
            except AttributeError:
                raise AttributeError("Unassigned reference '{}'."
                                     .format(self._name)) from None
            obj = ref()
            if obj is None:
                # reconstruct obj
                try:
                    obj = self.ref_type[uid]
                except TypeError:
                    msg = (f"Can't reconstruct '{self.ref_type}' instance "
                           "from id.")
                    raise AttributeError(msg) from None
                # renew reference
                setattr(instance, self._priv_member, (uid, WeakRef(obj)))
            return obj

    def __set__(self, instance: object, value: Component) -> None:
        """Set value of managed attribute to reference `value`."""
        self._check_immutable(instance)
        setattr(instance, self._priv_member,
                (UniqueIdentifier[value], WeakRef(value)))

    def __delete__(self, instance: object) -> None:
        """Remove value of managed reference."""
        if self._immutable or isinstance(instance, Immutable):
            raise AttributeError("Can't delete immutable attribute '{}'."
                                 .format(self._name))
        try:
            delattr(instance, self._priv_member)
        except AttributeError:
            pass


def ref(ref_type: Type[Component], *, immutable: bool = False,
        doc: Optional[Text] = None) -> Reference[Component]:
    return Reference[ref_type](immutable=immutable, doc=doc)
