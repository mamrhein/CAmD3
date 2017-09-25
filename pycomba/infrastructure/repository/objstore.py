# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        objstore
# Purpose:     Abstract base class for object stores
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


"""Abstract base class for object stores"""


# standard library imports
from abc import abstractmethod
from typing import Container, Sized

# third-party imports


# local imports
from ..component import Component, implementer


@implementer(Container, Sized)
class ObjectStore(Component):

    __slots__ = ()

    def __contains__(self, key):
        """key in self"""
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    @abstractmethod
    def __getitem__(self, key):
        """self[key]"""
        raise KeyError

    @abstractmethod
    def __setitem__(self, key, value):
        """self[key] = value"""
        raise KeyError

    @abstractmethod
    def __delitem__(self, key):
        """del self[key]"""
        raise KeyError
