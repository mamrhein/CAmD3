# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        domain
# Purpose:     Base classes for domain driven design
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

"""Base classes for domain driven design"""

# standard lib imports
from abc import abstractmethod
from typing import Any, Tuple

# local imports
from ..component import (AbstractAttribute, Component, Immutable,
                         StateChangedNotifyer)
from ...gbbs.tools import all_slot_attrs


class Entity(Component):

    """Abstract base class for entities.

    An Entity is an object that is primarily defined by its identity."""

    id = AbstractAttribute(immutable=True,
                           doc="Attribute representing the "
                               "identity of the entity.")

    # TODO: add version to allow pickling / unpickling instances with
    # different state caused by adding / removing attributes

    @abstractmethod
    def __init__(self, id: Any = None):
        """Initialize entity."""
        if id is None:
            self.__class__.id.set_once(self)
        else:
            self.id = id

    def __eq__(self, other: Any) -> bool:
        """self == other

        Entities are only equal if they are identical.
        """
        return self is other

    def __hash__(self) -> int:
        """hash(self)"""
        return id(self)

    def __setattr__(self, name: str, value: Any) -> None:
        """setattr(self, name, value)"""
        super().__setattr__(name, value)
        try:
            self.__dict__[name]
        except KeyError:
            pass
        else:
            if self.initialized:
                self.state_changed()

    # def __getstate__(self):
    #     """Return the entity's state."""
    # TODO: add version

    # def __setstate__(self, state: Mapping[str, Any]):
    #     """Set the entity's state."""
    #  TODO: reconstruct version specific

    def state_changed(self) -> None:
        """Signal 'state changed' to interested components."""
        try:
            notifyer = StateChangedNotifyer[self]
        except ValueError:
            pass
        else:
            notifyer.notify_state_changed(self)


class ValueObject(Component, Immutable):

    """Base class for 'value objects'.

    Value objects are immutable and hashable. Two instances compare equal if
    their classes and their states are equal."""

    __slots__ = ()

    def __getstate__(self) -> Tuple:
        """Return the state of the value object."""
        # get all attributes defined via __slots__ ...
        attrs = tuple(all_slot_attrs(self))
        # return the tuple of attribute values, ordered by attribute names
        return tuple(value for (attr, value) in sorted(attrs))

    def __setstate__(self, state: Tuple) -> None:
        """Reconstruct the state of the value object."""
        # get all attributes defined via __slots__ ...
        attrs = tuple(all_slot_attrs(self))
        assert isinstance(state, tuple), "Given state must be a tuple."
        if len(attrs) == len(state):
            for ((attr, _), value) in zip(sorted(attrs), state):
                setattr(self, attr, value)
        else:
            raise ValueError("Given state doesn't match number of attributes "
                             "of '" + self.__class__.__name__ + "' instance.")

    def __eq__(self, other: Any) -> bool:
        """self == other"""
        return (self.__class__ == other.__class__ and
                self.__getstate__() == other.__getstate__())

    def __hash__(self) -> int:
        """hash(self)"""
        return hash((self.__class__, self.__getstate__()))
