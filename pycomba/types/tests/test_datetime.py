#!usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        test_datetime
# Purpose:     Test driver for module datetime.
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


"""Test driver for module datetime."""


import unittest
from datetime import datetime, timedelta, tzinfo
from pycomba.types.datetime import datetime2timestamp, timestamp2datetime


class UTC(tzinfo):

    def utcoffset(self, dt):
        return timedelta(hours=0)

    def tzname(self, dt):
        return str("UST")

    def dst(self, dt):
        return timedelta(hours=0)

utc = UTC()


class CEST(tzinfo):

    def utcoffset(self, dt):
        return timedelta(hours=2)

    def tzname(self, dt):
        return str("CEST")

    def dst(self, dt):
        return timedelta(hours=1)

cest = CEST()


class ConversionTest(unittest.TestCase):

    def testDateTime(self):
        # naive datetime, conversion truncated to seconds
        dt = datetime.now()
        tst = datetime2timestamp(dt)
        rdt = timestamp2datetime(tst)
        self.assertTrue(isinstance(rdt, datetime))
        self.assertEqual(dt.replace(microsecond=0), rdt)
        # non-naive datetime, conversion truncated to seconds
        dt = datetime.now(cest)
        tst = datetime2timestamp(dt)
        rdt = timestamp2datetime(tst)
        self.assertTrue(isinstance(rdt, datetime))
        # timestamp2datetime returns UTC timestamp as naive datetime;
        # to compare it we have to convert it to UTC-aware
        rdt = rdt.replace(tzinfo=utc)
        self.assertEqual(dt.replace(microsecond=0), rdt)
        # naive datetime with microseconds
        dt = datetime.now()
        tst = datetime2timestamp(dt, trunc_to_seconds=False)
        rdt = timestamp2datetime(tst, trunc_to_seconds=False)
        self.assertTrue(isinstance(rdt, datetime))
        # in Py3 converting from timestamp to datetime truncates the
        # fractional part of the timestamp, so it may loose a microsecond
        # when converting back and forth
        self.assertTrue(abs(dt - rdt) <= timedelta(0, 0, 1))
        # non-naive datetime
        dt = datetime.now(cest)
        tst = datetime2timestamp(dt, trunc_to_seconds=False)
        rdt = timestamp2datetime(tst, trunc_to_seconds=False)
        self.assertTrue(isinstance(rdt, datetime))
        # see above
        rdt = rdt.replace(tzinfo=utc)
        # see above
        self.assertTrue(abs(dt - rdt) <= timedelta(0, 0, 1))


if __name__ == '__main__':
    unittest.main()
