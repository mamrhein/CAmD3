# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        extension
# Purpose:     Base classes for defining extensions of other classes.
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2016 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Base classes for defining extensions of other classes."""


from abc import abstractmethod
from typing import Any
from .component import Component


class Extension(Component):

    """Abstract base class for extensions."""

    __slots__ = ()

    @classmethod
    def __init_subclass__(cls, **kwds: Any) -> None:
        meth = cls.get_from                 # # get bound method 'get_from'
        if 'get_from' in cls.__dict__:      # if 'get_from' defined in cls,
            adapter = meth                  # we can use it as adapter,
        else:                               # otherwise we have to wrap it
            adapter = lambda obj: meth(obj)
            adapter.__annotations__['obj'] = object
        # need to set the return type here, because the class is not yet
        # defined in the surrounding namespace so that the evaluation of
        # the return type from a string does not work
        adapter.__annotations__['return'] = cls
        # add as adapter
        cls.add_adapter(adapter)

    @classmethod
    @abstractmethod
    def get_from(cls, obj: object) -> 'Extension':
        """Obtain extension from `obj`."""

    @abstractmethod
    def attach_to(self, obj: object) -> None:
        """Attach extension to `obj`."""


class StateExtension(Extension):

    """Abstract base class for extension which extend the state of an
    object."""

    __slots__ = ()

    @classmethod
    @abstractmethod
    def _namespace(cls):
        return '.'.join((cls.__module__, cls.__name__))

    @classmethod
    def get_from(cls, obj: object) -> 'StateExtension':
        """Obtain state extension from `obj`."""
        try:
            dict_ = obj.__dict__
        except AttributeError:
            pass
        else:
            try:
                return dict_[cls._namespace()]
            except KeyError:
                pass
        raise ValueError("%r does not have an extension of type '%s'." %
                         (obj, cls.__name__))

    def attach_to(self, obj: object) -> None:
        """Extend state of `obj`."""
        try:
            dict_ = obj.__dict__
        except AttributeError:
            pass
        else:
            try:
                dict_[self._namespace()] = self
            except:
                pass
            else:
                return
        raise TypeError("Instance of '%s' cannot be extended." %
                        obj.__class__.__name__,)
