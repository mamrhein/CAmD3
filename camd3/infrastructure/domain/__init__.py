# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        domain package
# Purpose:     Base classes for domain driven design
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


"""Base classes for domain driven design"""


from .domain import Entity, ValueObject


__all__ = [
    #domain
    'Entity',
    'ValueObject',
]
