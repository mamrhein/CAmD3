# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        __init__
# Purpose:     Basic types
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


"""Basic types"""


import sys
from importlib import import_module

# # Make some packages with basic types available through pycomba.types.

ns = globals()
for name, alias in (
        ('decimalfp', 'decimal'),
        ('quantity.money', 'money'),
        #('quantity.predefined', None),
        ('quantity', None),):
    alias = alias or name
    path = '.'.join((__name__, alias))
    mod = import_module(name)
    sys.modules[path] = mod
    #ns[alias] = mod

# clean-up namespace
del ns, name, alias, path, mod
del import_module
del sys
