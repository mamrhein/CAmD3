# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        datetime
# Purpose:     Date and Time arithmetics and conversions
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


"""Date and Time arithmetics and conversions"""


from math import floor
from calendar import timegm
from datetime import datetime


def timestamp2datetime(t, trunc_to_seconds=True):
    """Convert UTC timestamp (seconds since the epoch) to datetime."""
    if trunc_to_seconds:
        return datetime.utcfromtimestamp(floor(t))
    return datetime.utcfromtimestamp(t)


def datetime2timestamp(dt, trunc_to_seconds=True):
    """Convert datetime to UTC timestamp (seconds since the epoch)."""
    if trunc_to_seconds:
        return timegm(dt.utctimetuple())
    return timegm(dt.utctimetuple()) + dt.microsecond / 1e6


__all__ = [
    'datetime2timestamp',
    'timestamp2datetime',
]
