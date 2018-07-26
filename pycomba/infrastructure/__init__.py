# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        infrastructure package
# Purpose:     Basic infrastructure
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


"""Basic infrastructure"""


from .component import (AbstractAttribute, Attribute, Component, Immutable,
                        immutable, implementer, get_utility,
                        register_factory, register_utility)
from .domain import Entity, ValueObject


__all__ = [
    # component
    'AbstractAttribute',
    'Attribute',
    'Component',
    'Immutable',
    'immutable',
    'implementer',
    'get_utility',
    'register_factory',
    'register_utility',
    # domain
    'Entity',
    'ValueObject',
]
