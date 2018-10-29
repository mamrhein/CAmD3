# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        uid
# Purpose:     Base for (universally) unique identifiers
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2018 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Base for (universally) unique identifiers"""


# standard library imports
from uuid import UUID
from typing import Any

# third-party imports


# local imports
from .component import Component
from .immutable import immutable


@immutable
class UniqueIdentifier(Component):

    """Abstract base class for (universally) unique identifiers"""

    __slots__ = ()

    @classmethod
    def adapt(cls, obj: Any) -> 'UniqueIdentifier':
        try:
            return type(cls).adapt(cls, obj)
        except TypeError as exc:
            try:
                id = obj.id
            except AttributeError:
                raise exc from None
            try:
                return type(cls).adapt(cls, id)
            except TypeError:
                raise exc from None


UniqueIdentifier.register(UUID)


__all__ = [
    'UniqueIdentifier',
]
