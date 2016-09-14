# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        exceptions
# Purpose:     Special exceptions for component infrastructure
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


"""Special exceptions for component infrastructure """


class ComponentRegisterError(TypeError):

    """A component could not be registered."""


class ComponentLookupError(LookupError):

    """A component could not be found."""
