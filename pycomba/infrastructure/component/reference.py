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
from typing import Any
from uuid import UUID
from weakref import ref

# third-party imports


# local imports
from . import Component, immutable


@immutable
class UniqueIdentifier(Component):

    """"""

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


class Reference(Component):

    """"""

    __slots__ = ('_refobj_type', '_refobj_uid', '_refobj_ref')

    def __init__(self, obj: Component) -> None:
        self._refobj_type = type(obj)
        self._refobj_uid = UniqueIdentifier[obj]
        self._refobj_ref = ref(obj)

    @property
    def _obj(self):
        obj = self._refobj_ref()
        if obj is not None:
            return obj
        return self._refobj_type[self._refobj_uid]

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass
        return getattr(self._refobj_obj, name)


def _ref2uid(ref: Reference) -> UniqueIdentifier:
    return ref._refobj_uid

UniqueIdentifier.add_adapter(_ref2uid)


def _ref2comp(ref: Reference) -> Component:
    return ref._obj

Component.add_adapter(_ref2comp)
