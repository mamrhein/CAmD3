# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        tools
# Purpose:     Commonly usable functions and classes
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2013 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Commonly usable functions and classes"""


from collections import ChainMap
from functools import partial
from itertools import chain


_notNone = lambda x: x is not None
filternotnone = partial(filter, _notNone)


# decorator for copying doc strings
def copydoc(from_cls_or_func):
    """Decorate class or function with the doc string of parameter."""
    doc = from_cls_or_func.__doc__

    def _copydoc(to_cls_or_func):
        # don't want to overwrite doc strings:
        if not to_cls_or_func.__doc__ and doc:
            if isinstance(to_cls_or_func, type):
                # __doc__ attribute of classes is read_only, so we have to
                # create a new class
                name, bases, cls_dict = (to_cls_or_func.__name__,
                                         to_cls_or_func.__bases__,
                                         dict(to_cls_or_func.__dict__))
                cls_dict['__doc__'] = doc
                to_cls_or_func = type(name, bases, cls_dict)
            else:
                to_cls_or_func.__doc__ = doc
        return to_cls_or_func

    return _copydoc


# subclass iterator
def iter_subclasses(cls, recursive=True):
    """Iterator over real and virtual subclasses of `cls`.

    If `recursive` is True, iterates recursively over subclasses of
    subclasses.

    Each subclass is returned only once, even if it is a subclass of more than
    one subclass.
    """
    try:
        virtual_subclasses = cls._abc_registry
    except AttributeError:
        it = iter(cls.__subclasses__())
    else:
        it = chain(cls.__subclasses__(), virtual_subclasses)
    seen = set()
    while True:
        try:
            subcls = next(it)
        except StopIteration:
            break
        if subcls in seen:
            continue
        yield subcls
        seen.add(subcls)
        if recursive:
            it = chain(it, iter_subclasses(subcls, recursive=recursive))


# attribute iterator
def iter_attrs(cls, attr_types=None):
    dict_ = ChainMap(*(base.__dict__ for base in cls.__mro__[:-1]))
    if attr_types:
        spec = lambda item: isinstance(item[1], attr_types)
        return filter(spec, dict_.items())
    return dict_.items()


# slot attribute retriever

UNDEF_ATTR = object()   # marker for undefined attribute values


def all_slot_attrs(obj):
    """Return iterator that yields name-value-pairs for attributes defined
    in __slots__ (odered by MRO)."""
    for cls in reversed(obj.__class__.__mro__[:-1]):
        try:
            slots = cls.__dict__['__slots__']
        except KeyError:
            pass
        else:
            for attr in slots:
                yield attr, getattr(obj, attr, UNDEF_ATTR)
