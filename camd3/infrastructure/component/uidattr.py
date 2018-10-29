# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        uidattr
# Purpose:     Unique ids as attributes of objects
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


"""Unique ids as attributes of objects"""


# standard library imports
from typing import Any, Optional, Text

# local imports
from .attribute import AbstractAttribute
from .idfactories import UUIDGenerator
from .registry import get_utility
from .uid import UniqueIdentifier


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
                raise AttributeError(f"Unassigned attribute '{self.name}'.") \
                    from None

    def set_once(self, instance: Any):
        try:
            getattr(instance, self._priv_member)
        except AttributeError:
            uid_gen = self._uid_gen
            if uid_gen is None:
                uid_gen = get_utility(UUIDGenerator)
            uid = next(uid_gen)
            setattr(instance, self._priv_member, uid)
        else:
            raise AttributeError(f"Can't modify immutable attribute "
                                 f"'{self.name}'.")
