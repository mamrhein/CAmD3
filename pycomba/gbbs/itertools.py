# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        itertools
# Purpose:     Commonly usable iterators
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


"""Commonly usable iterators"""


from itertools import chain, repeat
from .tools import filternotnone


def izipmapped(key, *iterables):
    """Yield tuples of elements from iterables that are mapped to the same
    value by function key (sorted by key(elem)).

    >>> l1 = ['a', 'x', 'zz']
    >>> l2 = ['a', 'f', 'zz', 'f']
    >>> l3 = ['b', 'zz']
    >>> key = lambda x: x
    >>> list(izipmapped(key, l1, l2, l3))
    [['a', 'a'], ['b'], ['f'], ['f'], ['x'], ['zz', 'zz', 'zz']]
    """
    nIterables = len(iterables)
    # sort iterables:
    sortedLists = []
    for it in iterables:
        sortedLists.append(sorted([(key(elem), elem) for elem in it]))
    # create iterators which compensate different length of iterables
    filler = repeat((None, None))
    iterators = [chain(it, filler) for it in sortedLists]
    # start iterators
    currElems = list(map(next, iterators))
    currKeys = [keyVal for (keyVal, elem) in currElems]
    notNoneKeys = filternotnone(currKeys)
    while notNoneKeys:                  # elements left?
        mappedElems = []
        minKeyVal = min(notNoneKeys)    # next key value
        for i in range(nIterables):
            keyVal, elem = currElems[i]
            if keyVal == minKeyVal:
                mappedElems.append(elem)
                currElems[i] = next(iterators[i])
                currKeys[i] = currElems[i][0]
        yield mappedElems
        notNoneKeys = filternotnone(currKeys)


def imapzipmapped(op, key, *iterables):
    """Yield op(t) for all t returned by izipmapped(key, *iterables).

    >>> l1 = ['a', 'x', 'zz']
    >>> l2 = ['a', 'f', 'zz', 'f']
    >>> l3 = ['b', 'zz']
    >>> key = lambda x: x
    >>> op = lambda it: reduce(lambda x, y: x + y, it)
    >>> list(imapzipmapped(op, key, l1, l2, l3))
    ['aa', 'b', 'f', 'f', 'x', 'zzzzzz']
    >>> op = lambda it: len(it)
    >>> list(imapzipmapped(op, key, l1, l2, l3))
    [2, 1, 1, 1, 1, 3]
    """
    for t in izipmapped(key, *iterables):
        yield op(t)
