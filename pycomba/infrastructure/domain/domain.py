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

# from abc import abstractmethod
from typing import Any, Tuple
from .idfactories import UUIDGenerator
from ..component import (AbstractAttribute, Attribute, Component, get_utility,
                         Immutable)
from ...gbbs.tools import all_slot_attrs


class Entity(Component):

    """Abstract base class for entities.

    An Entity is an object that is primarily defined by its identity."""

    id = AbstractAttribute(immutable=True,
                           doc="Attribute representing the "
                               "identity of the entity.")

    def __eq__(self, other: Any) -> bool:
        """self == other

        Entities are only equal if they are identical.
        """
        return self is other

    def __hash__(self) -> int:
        """hash(self)"""
        return id(self)


class AggregateRoot(Entity):

    """Abstract base class for aggregate roots.

    An AggregateRoot is an entity with globally unique identity. It may
    contain ('aggregate') other entities which are unique within the
    aggregate."""

    id = Attribute(immutable=True,
                   doc="Attribute representing the identity of the aggregate."
                   )

    def __new__(cls, *args, **kwds):
        self = super(AggregateRoot, cls).__new__(cls)
        uuidGen = get_utility(UUIDGenerator)
        self._id = next(uuidGen)
        return self


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
