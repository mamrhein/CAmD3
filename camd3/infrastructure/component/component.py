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
from itertools import chain
from typing import (Any, Callable, Iterable, MutableMapping,
                    MutableSequence, Sequence, Tuple)

# local imports
from .attribute import Attribute
from .exceptions import ComponentLookupError
from .immutable import Immutable
from .signature import _is_instance, _is_subclass, signature
from ...gbbs.tools import iter_subclasses


Adapter = Callable[[Any], 'Component']
_AdapterRegistry = MutableMapping[type, MutableSequence[Adapter]]


class _ABCSet(set):

    def __init__(self, it: Iterable[type] = ()) -> None:
        for elem in it:
            self.add(elem)

    def add(self, abc: type) -> None:
        to_be_removed = []
        for cls in self:
            if _is_subclass(cls, abc):
                return      # we already have a more specific type
            if _is_subclass(abc, cls):
                # replace type by more specific one
                # (we can't do that directly while iterating over the set)
                to_be_removed.append(cls)
        super().add(abc)
        for cls in to_be_removed:
            self.remove(cls)


INIT_MARKER = '@'


class ComponentMeta(ABCMeta):

    """Meta class to create components.

    Args:
        cls_name(str): name of new component
        bases(Tuple[type, ...]): base classes
        namespace(Mapping[str, Any]): namespace of new component
        **kwds (Any): additional class statement args

    Returns:
        ComponentMeta: new component class
    """

    def __new__(metacls, cls_name: str, bases: Tuple[type, ...],
                namespace: MutableMapping[str, Any],
                **kwds: Any) -> 'ComponentMeta':
        # force __slots__ for attribute of immutable components
        if any(issubclass(cls, Immutable) for cls in bases):
            all_bases = set(chain(*(cls.__mro__[:-1] for cls in bases
                                    if cls is not object)))
            if any('__slots__' not in cls.__dict__
                   for cls in all_bases):
                raise TypeError("All base classes of '" + cls_name +
                                "' must have an attribute '__slots__'.")
            slots = namespace.get('__slots__', ())
            new_slots = []
            for name, attr in namespace.items():
                if isinstance(attr, Attribute):
                    # type.__new__ will call __set_name__ later, but we
                    # need to do it here in order to get the private member
                    # names
                    attr.__set_name__(None, name)
                    priv_member = attr._priv_member
                    if priv_member not in slots:
                        new_slots.append(priv_member)
            namespace['__slots__'] = tuple(chain(slots, new_slots))
        # create class
        cls = super().__new__(metacls, cls_name, bases, namespace, **kwds)
        # now the new class is ready
        return cls

    @classmethod
    def __prepare__(metacls, name: str, bases: Tuple[type, ...],
                    **kwds: Any) -> MutableMapping:
        namespace = {}
        # additional class attributes
        adapter_registry = {}   # type: _AdapterRegistry
        namespace['__virtual_bases__'] = _ABCSet()
        namespace['__adapters__'] = adapter_registry
        return namespace

    def __call__(cls, *args, **kwds) -> 'Component':
        """Return new instance of `cls`."""
        comp = cls.__new__(cls, *args, **kwds)
        if isinstance(comp, cls):
            # mark instance as 'not yet initialized' (if it has a __dict__)
            try:
                comp.__dict__[INIT_MARKER] = True
            except AttributeError:
                pass
            comp.__init__(*args, **kwds)
            # remove marker
            try:
                del comp.__dict__[INIT_MARKER]
            except AttributeError:
                pass
        return comp

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
            raise TypeError(f"Cannot adapt instance of type '{type(obj)}' "
                            f"to '{cls.__name__ }'.")
        else:
            try:
                return adapter(obj)
            except TypeError:
                raise TypeError(f"Cannot adapt instance of type '{type(obj)}'"
                                f" to '{cls.__name__ }'.")
            except Exception:
                raise ValueError(f"Cannot adapt given object '{repr(obj)}' "
                                 f"to '{cls.__name__}'.")

    @property
    def attr_names(cls) -> Tuple[str, ...]:
        """Return the names of all attributes defined by the component (in
        definition order).
        """
        return tuple(name for name, item in cls.__dict__.items()
                     if isinstance(item, Attribute))

    @property
    def all_attr_names(cls) -> Tuple[str, ...]:
        """Return the names of all attributes defined by the component and its
        base components (in definition order).
        """
        seen = {}
        return tuple(seen.setdefault(name, name)
                     for name in chain(*(acls.attr_names
                                         for acls
                                         in reversed(cls.__mro__[:-1])
                                         if issubclass(acls, Component)))
                     if name not in seen)

    def register(cls, subcls: type):
        """Register a virtual subclass of the component."""
        try:
            subcls.__virtual_bases__.add(cls)
        except AttributeError:      # `subcls` is not a component,
            pass                    # so go without a back reference
        return super().register(subcls)

    def add_adapter(cls, adapter: Adapter) -> Adapter:
        """Add `adapter` to the list of adapters providing an instance of
        `cls`."""
        sgn = signature(adapter)
        return_type = sgn.return_type
        assert _is_subclass(return_type, cls), \
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

    def _iter_adapters(cls) -> Iterable[Tuple[type, Adapter]]:
        """Return an iterable of type / adapter pairs"""
        for required, adapters in cls.__adapters__.items():
            if adapters:
                yield required, adapters[-1]
        for subcls in iter_subclasses(cls):
            try:
                items = subcls.__adapters__.items()
            except AttributeError:
                pass
            else:
                for required, adapters in items:
                    if adapters:
                        yield required, adapters[-1]

    def get_adapter(cls, obj: Any) -> Adapter:
        """Return an adapter adapting `obj` to the interface defined by `cls`.
        """
        type_found = None
        adapter_found = None
        for required, adapter in cls._iter_adapters():
            if _is_instance(obj, required):
                if not type_found or _is_subclass(required, type_found):
                    # required is more specific
                    type_found, adapter_found = required, adapter
        if type_found:
            return adapter_found
        raise ComponentLookupError(f"'{cls.__name__}: no adapter for "
                                   f"'{repr(obj)}' found.")

    def __repr__(cls):
        """repr(cls)"""
        return f"{cls.__module__}.{cls.__qualname__}"


class Component(metaclass=ComponentMeta):

    """Abstract base class for components."""

    __slots__ = ()

    @abstractmethod
    def __init__(self, *args, **kwds) -> None:
        """Initialize instance of component."""

    @property
    def initialized(self):
        """Return `True` if `self` is initialized, `False` otherwise.

        Initialized means that either
        * `self.__init__` has been called and has returned, or
        * the components subclass `__new__` method did not return an instance
          of that class (and `self.__init__` therefor has not been called).
        """
        try:
            self.__dict__[INIT_MARKER]
        except (AttributeError, KeyError):
            return True
        else:
            return False


def implementer(*interfaces: type) -> Callable[[type], type]:
    """Class decorator registering a class that implements the given
    interfaces.

    It also sets doc strings of methods of the class having no doc string to
    the doc string of the corresponding method from interfaces.
    """
    def _register_cls(cls: type) -> type:
        for interface in interfaces:
            interface.register(cls)
        it = ((name, member) for name, member in cls.__dict__.items()
              if callable(member) and member.__doc__ is None)
        for name, member in it:
            for interface in interfaces:
                try:
                    doc = getattr(interface, name).__doc__
                except AttributeError:
                    pass
                else:
                    member.__doc__ = doc
                    break
        return cls
    return _register_cls


__all__ = [
    'Component',
    'implementer',
]
