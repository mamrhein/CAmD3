# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        registry
# Purpose:     Component registry
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


"""Component registry"""


from typing import Any, Callable, Dict, List, Optional, Tuple
from .exceptions import ComponentRegisterError, ComponentLookupError
from .signature import signature
from ...gbbs.tools import iter_subclasses


# some types
_FactoryFunc = Callable[[], Any]
_FactoryDict = Dict[Tuple[type, Optional[str]], List[_FactoryFunc]]
_UtilityFunc = Callable
_UtilityDict = Dict[Tuple[type, Optional[str]], List[_UtilityFunc]]


class ComponentRegistry:

    """"""

    def __init__(self) -> None:
        self._factories = {}        # type: _FactoryDict
        self._utilities = {}        # type: _UtilityDict

    def register_factory(self, factory: _FactoryFunc,
                         interface: type = None, name: str = None) -> None:
        if interface is None:
            sgn = signature(factory)
            interface = sgn.return_type
        if interface:
            try:
                self._factories[(interface, name)].append(factory)
            except KeyError:
                self._factories[(interface, name)] = [factory]
        else:
            raise ComponentRegisterError("Couldn't determine interface of "
                                         "objects build by '{}'"
                                         .format(factory))

    def register_utility(self, utility: _UtilityFunc,
                         interface: type = None, name: str = None) -> None:
        if interface is None:
            if not isinstance(utility, type):
                raise ComponentRegisterError("If no `interface` is given, "
                                             "`utility` must be a class.")
            interface = utility
        try:
            self._utilities[(interface, name)].append(utility)
        except KeyError:
            self._utilities[(interface, name)] = [utility]

    def _lookup_utility(self, interface: type, name: str = None) \
            -> _UtilityFunc:
        try:
            return self._utilities[(interface, name)][-1]
        except KeyError:
            try:        # do we have a factory?
                factory = self._factories[(interface, name)][-1]
            except KeyError:
                pass
            else:
                return factory()
        raise LookupError

    def get_utility(self, interface: type, name: str = None) \
            -> _UtilityFunc:
        try:
            return self._lookup_utility(interface, name)
        except LookupError:
            for subcls in iter_subclasses(interface):
                try:
                    return self._lookup_utility(subcls, name)
                except LookupError:
                    pass
        raise ComponentLookupError("No utility registered for the given "
                                   "interface under the given name.")


# registry
_comp_registry = ComponentRegistry()


def get_component_registry():
    return _comp_registry


# helper functions for registration and retrieval of components


def register_factory(factory: _FactoryFunc, interface: type = None,
                     name: str = None) -> None:
    """Register given `factory` as factory for obejcts that provide the
    given interface."""
    reg = get_component_registry()
    reg.register_factory(factory, interface, name)


def register_utility(utility: _UtilityFunc, interface: type = None,
                     name: str = None) -> None:
    """Register a utility which provides the given interface."""
    reg = get_component_registry()
    reg.register_utility(utility, interface, name)


def get_utility(interface: type, name: str = None) -> _UtilityFunc:
    """Retrieve a utility which provides the given interface."""
    reg = get_component_registry()
    return reg.get_utility(interface, name)
