# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        immutable
# Purpose:     Abstract base class for immutable objects.
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2014 ff. Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Abstract base class for immutable objects."""


from abc import ABCMeta
from collections import Set
from numbers import Number


class Immutable(metaclass=ABCMeta):

    """Abstract base class for immutable objects.

    Note: This class is used to register classes that create immutable
    instances as virtual subclasses. It does not make instances immutable!"""

    __slots__ = ()

    def __copy__(self) -> 'Immutable':
        """copy(self)"""
        return self

    def __deepcopy__(self) -> 'Immutable':
        """deepcopy(self)"""
        return self

Immutable.register(Number)  # type: ignore
Immutable.register(bytes)   # type: ignore
Immutable.register(str)     # type: ignore
Immutable.register(Set)     # type: ignore


def is_immutable(obj: object) -> bool:
    """Return True if obj is immutable, otherwise False."""
    if isinstance(obj, tuple):
        try:
            hash(obj)
        except TypeError:
            return False
        else:
            return True
    return isinstance(obj, Immutable)


def immutable(cls: type) -> type:
    """Register `cls` as class creating immutable objects."""
    Immutable.register(cls)     # type: ignore
    return cls
