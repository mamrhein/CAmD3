# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        specification package
# Purpose:     Base classes for specifications
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


"""Base classes for specifications"""


from .specification import (
    Specification, ValueSpecification, IntervalSpecification)


__all__ = [
    'Specification',
    'ValueSpecification',
    'IntervalSpecification',
]
