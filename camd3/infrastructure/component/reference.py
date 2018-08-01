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
from typing import Any, Dict, Iterator, Optional, Text, Tuple, Type
from weakref import ref as WeakRef

# third-party imports


# local imports
from . import Component, get_utility, Immutable, UniqueIdentifier
from .attribute import AbstractAttribute
from ..domain import UUIDGenerator


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
        if cls._ref_type is None:
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


class _Ref(Immutable):

    """Helper class to store the privat state of references."""

    __slots__ = ('_uid', '_ref')

    def __init__(self, obj: Component) -> None:
        self._uid = UniqueIdentifier[obj]
        self._ref = WeakRef(obj)

    @property
    def uid(self):
        return self._uid

    @property
    def ref(self):
        return self._ref

    def __call__(self):
        return self._ref()

    def __getstate__(self) -> Tuple:
        return (self._uid,)

    def __setstate__(self, state: Tuple) -> None:
        self._uid = state[0]
        self._ref = type(None)         # dummy weakref


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
                ref = getattr(instance, self._priv_member)
            except AttributeError:
                raise AttributeError("Unassigned reference '{}'."
                                     .format(self._name)) from None

            obj = ref()
            if obj is None:
                uid = ref.uid
                # reconstruct obj
                try:
                    obj = self.ref_type[uid]
                except TypeError:
                    msg = (f"Can't reconstruct '{self.ref_type}' instance "
                           "from id.")
                    raise AttributeError(msg) from None
                # renew reference
                setattr(instance, self._priv_member, _Ref(obj))
            return obj

    def __set__(self, instance: object, value: Component) -> None:
        """Set value of managed attribute to reference `value`."""
        self._check_immutable(instance)
        setattr(instance, self._priv_member, _Ref(value))

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


class UniqueIdAttribute(AbstractAttribute):

    """Descriptor class for defining unique ids as attributes of objects."""

    __isabstractmethod__ = False

    def __init__(self, *,
                 uid_gen: Optional[UUIDGenerator] = None,
                 doc: Optional[Text] = 'Unique id.') -> None:
        """Initialze attribute."""
        super().__init__(immutable=True, doc=doc)
        self._uid_gen = uid_gen

    def __get__(self, instance: Any, owner: type) -> UniqueIdentifier:
        """Return unique id."""
        if instance is None:    # if accessed via class, return descriptor
            return self         # (i.e. self),
        else:                   # else return unique id
            try:
                return getattr(instance, self._priv_member)
            except AttributeError:
                uid_gen = self._uid_gen
                if uid_gen is None:
                    uid_gen = get_utility(UUIDGenerator)
                uid = next(uid_gen)
                setattr(instance, self._priv_member, uid)
                return uid
