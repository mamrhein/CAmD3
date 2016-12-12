# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        component
# Purpose:     Basic component infrastructure
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2014 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Basic component infrastructure"""


# standard lib imports
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from itertools import chain
import types
from typing import (Any, Callable, Iterable, MutableMapping, Sequence, Tuple)

# local imports
from .attribute import Attribute
from .exceptions import ComponentLookupError
from .immutable import Immutable
from .signature import signature


class _ABCSet(set):

    def __init__(self, it: Iterable[type] = ()) -> None:
        for elem in it:
            self.add(elem)

    def add(self, abc: type) -> None:
        to_be_removed = []
        for cls in self:
            if issubclass(cls, abc):
                return      # we already have a more specific type
            if issubclass(abc, cls):
                # replace type by more specific one
                # (we can't do that directly while iterating over the set)
                to_be_removed.append(cls)
        super().add(abc)
        for cls in to_be_removed:
            self.remove(cls)


class ComponentMeta(ABCMeta):

    """Meta class to create components.

    Args:
        cls_name(str): name of new component
        bases(Tuple[type, ...]): base classes
        namespace(Mapping[str, Any]): namespace of new component

    Returns:
        ComponentMeta: new component class
    """

    def __new__(metacls, cls_name: str, bases: Tuple[type, ...],
                namespace: MutableMapping[str, Any],
                **kwds: Any) -> 'ComponentMeta':
        # turn __init_subclass__ into a classmethod if it is defined as
        # instance method
        init_subclass = namespace.get('__init_subclass__')  # type: Callable
        if isinstance(init_subclass, types.FunctionType):
            namespace['__init_subclass__'] = classmethod(init_subclass)
        # save definition order
        namespace['__definition_order__'] = tuple(namespace)
        # set name of descriptors which have a __set_name__ method
        for name, attr in namespace.items():
            try:
                attr.__set_name__(name)
            except AttributeError:
                pass
        # force __slots__ for immutable components
        if any(issubclass(cls, Immutable) for cls in bases):
            metacls._init_slots(cls_name, bases, namespace)
        # create class
        cls = super().__new__(metacls, cls_name, bases, namespace)
        # additional class attributes
        cls.__virtual_bases__ = _ABCSet()
        cls.__adapters__ = {}   # type: Dict[type, MutableSequence[Callable]]
        # call __init_subclass__ of direct superclass
        try:
            init_subclass = super(cls, cls).__init_subclass__
        except AttributeError:
            pass
        else:
            init_subclass(**kwds)
        # now the new class is ready
        return cls

    @classmethod
    def __prepare__(metacls, name: str, bases: Tuple[type, ...],
                    **kwds: Any) -> MutableMapping:
        return OrderedDict()

    def __init__(cls, cls_name: str, bases: Tuple[type, ...],
                 namespace: MutableMapping[str, Any],
                 **kwds: Any) -> None:
        super().__init__(cls_name, bases, namespace)

    @property
    def definition_order(cls):
        return cls.__definition_order__

    @classmethod
    def _init_slots(metacls, cls_name: str, bases: Tuple[type, ...],
                    namespace: MutableMapping[str, Any]) -> None:
        all_bases = set(chain(*(cls.__mro__[:-1] for cls in bases
                                if cls is not object)))
        if any('__slots__' not in cls.__dict__
               for cls in all_bases):
            raise TypeError("All base classes of '" + cls_name +
                            "' must have an attribute '__slots__'.")
        slots = namespace.get('__slots__', ())
        new_slots = (attr._priv_member
                     for attr in namespace.values()
                     if isinstance(attr, Attribute) and
                     attr._priv_member not in slots)
        namespace['__slots__'] = tuple(slots) + tuple(new_slots)

    def __dir__(cls) -> Sequence[str]:
        """dir(cls)"""
        return sorted(set(chain(dir(type(cls)), *(ns.__dict__.keys()
                                                  for ns in cls.__mro__))))

    def __getitem__(cls, obj: Any) -> 'Component':
        """Shortcut for cls.adapt(obj)."""
        return cls.adapt(obj)

    def adapt(cls, obj: Any) -> 'Component':
        """Return an object adapting `obj` to the interface defined by
        `cls`."""
        if isinstance(obj, cls):
            # obj provides the interface, so just return it
            return obj
        # look for adapter adapting obj to interface
        try:
            adapter = cls.get_adapter(obj)
        except ComponentLookupError:
            pass
        else:
            return adapter(obj)
        raise TypeError("Cannot adapt given object '" + repr(obj) + "' to '" +
                        cls.__name__ + "'.")

    @property
    def attr_names(cls) -> Tuple[str, ...]:
        """Return the names of all attributes defined by the component (in
        definition order).
        """
        return tuple(name for name in cls.definition_order
                     if isinstance(getattr(cls, name), Attribute))

    @property
    def all_attr_names(cls) -> Tuple[str, ...]:
        """Return the names of all attributes defined by the component and its
        base components (in definition order).
        """
        seen = {}
        return tuple(seen.setdefault(name, name)
                     for name in chain(*(acls.definition_order
                                         for acls
                                         in reversed(cls.__mro__[:-1])
                                         if issubclass(acls, Component)))
                     if name not in seen and
                     isinstance(getattr(cls, name), Attribute))

    def register(cls, subcls: type):
        """Register a virtual subclass of the component."""
        try:
            subcls.__virtual_bases__.add(cls)
        except AttributeError:      # `subcls` is not a component,
            pass                    # so go without a back reference
        return super().register(subcls)

    def add_adapter(cls, adapter: Callable[[Any], 'ComponentMeta']) \
            -> Callable[[Any], 'ComponentMeta']:
        sgn = signature(adapter)
        return_type = sgn.return_type
        assert issubclass(return_type, cls), \
            "Adapter returns instance of '{}', not a subclass of '{}'".format(
                return_type, cls)
        arg_types, var_arg_type = sgn.arg_types, sgn.var_arg_type
        assert var_arg_type is None and len(arg_types) == 1, \
            "Adapter must have exactly 1 argument."
        arg_type = arg_types[0]
        try:
            adapters = cls.__adapters__[arg_type]
        except KeyError:
            cls.__adapters__[arg_type] = [adapter]
        else:
            if adapter not in adapters:
                adapters.append(adapter)
        return adapter

    def get_adapter(cls, obj):
        """Return adapter adapting `obj` to the interface defined by `cls`."""
        # FIXME: make the algo more deterministic
        look_for = type(obj)
        found = None
        for required, adapters in cls.__adapters__.items():
            if issubclass(look_for, required):
                if not found or issubclass(required, found):
                    # required is more specific
                    found, adapter = required, adapters[0]
        if found:
            return adapter
        raise ComponentLookupError("'" + cls.__name__ +
                                   "': no adapter for '" +
                                   repr(obj) + "' found.")


class Component(metaclass=ComponentMeta):

    """Abstract base class for components."""

    __slots__ = ()

    @abstractmethod
    def __init__(self, *args, **kwds) -> None:
        """Initialize instance of component."""


def implementer(*interfaces: type) -> Callable[[type], type]:
    """Class decorator registering a class that implements the given
    interfaces."""

    def _register_cls(cls: type) -> type:
        for interface in interfaces:
            interface.register(cls)
        return cls

    return _register_cls


__all__ = [
    'Component',
    'implementer',
]
