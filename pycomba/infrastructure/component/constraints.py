# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        attribute
# Purpose:     Base classes and functions for defining constraints
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


"""Base classes and functions for defining constraints"""


from functools import partial
from numbers import Number, Rational, Integral
import operator
from typing import Any, Callable, Sized


def subclass(*types: type) -> Callable[[Any], bool]:
    """Return function to be used as type constraint checker."""
    func = lambda value: issubclass(value, types)
    func.__doc__ = "Value of attribute '{}' must be a subclass of " \
                   + ' or '.join((cls.__name__ for cls in types)) + '.'
    return func


def instance(*types: type) -> Callable[[Any], bool]:
    """Return function to be used as type constraint checker."""
    func = lambda value: isinstance(value, types)
    func.__doc__ = "Value of attribute '{}' must be instance of " \
                   + ' or '.join((cls.__name__ for cls in types)) + '.'
    return func


is_number = instance(Number)
is_rational = instance(Rational)
is_int = instance(Integral)


def ValueConstraint(expr: str, op: Callable[..., bool], *fargs: Any) \
        -> Callable[..., Callable[..., bool]]:
    """Return factory for functions to be used as constraint checker."""
    def factory(*args):
        func = partial(op, *(fargs + args))
        func.__doc__ = "Value of attribute '{}' must be " \
                       + expr.format(*args) + '.'
        return func
    return factory


lt = ValueConstraint('< {}', operator.gt)
le = ValueConstraint('<= {}', operator.ge)
gt = ValueConstraint('> {}', operator.lt)
ge = ValueConstraint('>= {}', operator.le)
non_negative = ge(0)
between = ValueConstraint('>= {} and <= {}',
                          lambda lower, upper, value: lower <= value <= upper)


def LengthConstraint(expr: str, op: Callable[[int, int], bool]) \
        -> Callable[[int], Callable[[Sized], bool]]:
    """Return factory for functions to be used as constraint checker."""
    def factory(length):
        func = lambda value: op(len(value), length)
        func.__doc__ = "Length of attribute '{}' must be " \
                       + expr.format(length) + '.'
        return func
    return factory


length = LengthConstraint('= {}', operator.eq)
max_length = LengthConstraint('<= {}', operator.le)
min_length = LengthConstraint('>= {}', operator.ge)

# TODO: more constraints

__all__ = [
    'LengthConstraint',
    'ValueConstraint',
    'between',
    'ge',
    'gt',
    'instance',
    'is_int',
    'is_number',
    'is_rational',
    'le',
    'length',
    'lt',
    'max_length',
    'min_length',
    'non_negative',
    'subclass',
]
