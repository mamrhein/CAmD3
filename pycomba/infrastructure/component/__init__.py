# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        component package
# Purpose:     Basic component infrastructure
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


"""Basic component infrastructure"""


from .attribute import AbstractAttribute, Attribute
from .component import Component, implementer
from .constraints import (LengthConstraint,
                          ValueConstraint, between, ge, gt, instance, is_int,
                          is_number, is_rational, le, length, lt, max_length,
                          min_length, non_negative)
from .immutable import Immutable, immutable, is_immutable
from .registry import (ComponentLookupError, get_utility, register_factory,
                       register_utility)


__all__ = [
    # attribute
    'AbstractAttribute',
    'Attribute',
    # component
    'Component',
    'implementer',
    # constraints
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
    # immutable
    'Immutable',
    'immutable',
    'is_immutable',
    # registry
    'ComponentLookupError',
    'get_utility',
    'register_factory',
    'register_utility',
]
