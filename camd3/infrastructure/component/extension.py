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


# standard lib imports
from abc import abstractmethod
from typing import Any, Mapping, Optional
from weakref import WeakKeyDictionary

# local imports
from .component import Component


class Extension(Component):

    """Abstract base class for extensions."""

    __slots__ = ()

    @classmethod
    def __init_subclass__(cls, **kwds: Any) -> None:
        """Set-up adapter for sub-class."""
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
    def get_from(cls, obj: object) -> 'Extension':
        """Obtain extension from `obj`."""
        container = cls._get_mapping(obj)
        try:
            return container[cls._get_key(obj)]
        except TypeError:
            raise TypeError("Instance of '%s' cannot be extended." %
                            obj.__class__.__name__,) from None
        except KeyError:
            raise ValueError("%r does not have an extension of type '%s'." %
                             (obj, cls.__name__)) from None

    @classmethod
    def remove_from(cls, obj: object) -> None:
        """Remove extension from `obj`."""
        container = cls._get_mapping(obj)
        try:
            del container[cls._get_key(obj)]
        except TypeError:
            raise TypeError("Instance of '%s' cannot be extended." %
                            obj.__class__.__name__,) from None
        except KeyError:
            raise ValueError("%r does not have an extension of type '%s'." %
                             (obj, cls.__name__)) from None

    def attach_to(self, obj: object) -> None:
        """Attach extension to `obj`."""
        cls = self.__class__
        container = cls._get_mapping(obj)
        try:
            container[cls._get_key(obj)] = self
        except TypeError:
            raise TypeError("Instance of '%s' cannot be extended." %
                            obj.__class__.__name__,) from None

    @classmethod
    @abstractmethod
    def _get_mapping(cls, obj: Any) -> Optional[Mapping]:
        """Return the mapping which contains the extensions instance."""

    @classmethod
    @abstractmethod
    def _get_key(cls, obj: Any) -> Any:
        """Return the key under which the extensions instance is stored."""


class StateExtension(Extension):

    """Abstract base class for extensions which extend the state of an
    object."""

    __slots__ = ()

    @classmethod
    def __init_subclass__(cls, **kwds: Any) -> None:
        """Set-up the key under which the extensions instance is stored.

        Extends Extension.__init_subclass."""
        key = kwds.pop('key', None)
        super().__init_subclass__(**kwds)
        if key is None:
            try:
                cls._key
            except AttributeError:
                cls._key = '.'.join((cls.__module__, cls.__name__))
        else:
            cls._key = key

    @classmethod
    def _get_mapping(cls, obj: Any) -> Optional[Mapping]:
        """Return the mapping which contains the extensions instance."""
        return getattr(obj, '__dict__', None)

    @classmethod
    def _get_key(cls, obj: Any) -> Any:
        """Return the key under which the extensions instance is stored."""
        return cls._key


class TransientExtension(Extension):

    """Abstract base class for transient extension."""

    __slots__ = ()

    @classmethod
    def __init_subclass__(cls, **kwds: Any) -> None:
        """Set-up the mapping which contains the extensions instance.

        Extends Extension.__init_subclass__."""
        obj_map = kwds.pop('obj_map', None)
        super().__init_subclass__(**kwds)
        if obj_map is None:
            try:
                cls._obj_map
            except AttributeError:
                cls._obj_map = WeakKeyDictionary()
        else:
            cls._obj_map = obj_map

    @classmethod
    def _get_mapping(cls, obj: Any) -> Mapping:
        """Return the mapping which contains the extensions instance."""
        return cls._obj_map

    @classmethod
    def _get_key(cls, obj: Any) -> Any:
        """Return the key under which the extensions instance is stored."""
        return obj
