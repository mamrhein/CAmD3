# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        idfactories
# Purpose:     Factories for IDs
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


"""Factories for IDs"""


from abc import ABCMeta, abstractmethod
from itertools import count
from typing import (Any, Callable, Generator, Iterable, Iterator, Optional,
                    TypeVar)
from uuid import UUID, uuid1, uuid5


# some types
ID = TypeVar('ID', covariant=True)

IDGenerator = Iterator[ID]          # type of objects generating IDs
IDGenerator.register(Generator[ID, None, None])

UUIDGenerator = IDGenerator[UUID]   # type of objects generating UUIDs
UUIDGenerator.register(Generator[UUID, None, None])


# factory for UUIDGenerator
def uuid_generator() -> UUIDGenerator:
    """Return a generator for UUIDs."""
    namespace = uuid1()
    while True:
        yield uuid5(namespace, str(uuid1()))


class LocalIDGeneratorFactory(metaclass=ABCMeta):

    """Abstract factory for callables generating locally unique IDs."""

    @abstractmethod
    def __call__(self, context: Iterable, incrementor: Callable[[Any], Any]) \
            -> IDGenerator:
        """Create generator of locally unique IDs."""


# factory for IDGenerator
def local_id_generator(context: Iterable, incrementor: Callable[[Any], Any]) \
        -> IDGenerator:
    """Return a generator for IDs that are unique within a given `context`.

    The next ID is calculated by incrementing an ID value using the given
    `incrementor` function.

    The initial ID value is calculated as the maximum of the IDs of items in
    `context`."""
    try:
        id = max((item.id for item in context))
    except ValueError:
        id = None
    while True:
        id = incrementor(id)
        yield id


class LocalNumIDGeneratorFactory(metaclass=ABCMeta):

    """Abstract factory for callables generating locally unique numerical
    IDs.
    """

    @abstractmethod
    def __call__(self, context: Iterable = (), start: Optional[int] = None) \
            -> IDGenerator:
        """Create generator of locally unique numerical IDs."""


# factory for IDGenerator
def local_num_id_generator(context: Iterable = (),
                           start: Optional[int] = None) \
        -> IDGenerator:
    """Return a generator for IDs that are unique within a given `context`.

    The next id is calculated simply by incrementing a number by 1.

    The initial number can be set by explicitely giving a start value or by
    giving a context (i.e. an iterable of objects that have a numerical id).
    In the latter case the initial number is calculated as the maximum of the
    ids in context, incremented by 1. If neither a start value nor a context
    is given, the first id will be 1."""
    if start is None:
        try:
            start = max((elem.id for elem in context)) + 1
        except ValueError:
            start = 1
    else:
        if context:
            maxId = max((elem.id for elem in context))
            if maxId >= start:
                raise ValueError("Given start value (%s) is not greater than "
                                 "the greatest id in context (%s)." %
                                 (start, maxId))
    return count(start)
