#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_interval
# Purpose:     Test driver for module interval
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


import unittest
from copy import copy, deepcopy
from operator import delitem, setitem
from pycomba.types.interval import (Interval, InvalidInterval,
                                    LowerClosedInterval, UpperClosedInterval,
                                    LowerOpenInterval, UpperOpenInterval,
                                    ClosedInterval, OpenBoundedInterval,
                                    ChainableInterval,
                                    LowerInfiniteLimit, UpperInfiniteLimit,
                                    LowerClosedLimit, LowerOpenLimit,
                                    UpperClosedLimit, UpperOpenLimit,
                                    IntervalChain, IntervalMapping)


#TODO: write more tests


class IntervalTests(unittest.TestCase):

    def test_constructor(self):
        lower_limit = LowerClosedLimit(0)
        upper_limit = UpperClosedLimit(1)
        self.assertIsInstance(Interval(), Interval)
        self.assertIsInstance(Interval(lower_limit, upper_limit), Interval)
        self.assertIsInstance(Interval(lower_limit=lower_limit), Interval)
        self.assertIsInstance(Interval(upper_limit=upper_limit), Interval)
        # closed interval
        ival = Interval(lower_limit, upper_limit)
        self.assertIs(ival.lower_limit, lower_limit)
        self.assertIs(ival.upper_limit, upper_limit)
        self.assertEqual(ival.limits, (lower_limit, upper_limit))
        # upper open interval
        ival = Interval(lower_limit=lower_limit)
        self.assertIs(ival.lower_limit, lower_limit)
        self.assertIs(ival.upper_limit, UpperInfiniteLimit())
        self.assertEqual(ival.limits, (lower_limit, UpperInfiniteLimit()))
        # lower open interval
        ival = Interval(upper_limit=upper_limit)
        self.assertIs(ival.lower_limit, LowerInfiniteLimit())
        self.assertIs(ival.upper_limit, upper_limit)
        self.assertEqual(ival.limits, (LowerInfiniteLimit(), upper_limit))
        # unbounded interval
        ival = Interval()
        self.assertIs(ival.lower_limit, LowerInfiniteLimit())
        self.assertIs(ival.upper_limit, UpperInfiniteLimit())
        self.assertEqual(ival.limits, (LowerInfiniteLimit(),
                                       UpperInfiniteLimit()))
        # invalid limits
        self.assertRaises(InvalidInterval, Interval, lower_limit=upper_limit)
        self.assertRaises(InvalidInterval, Interval, upper_limit=lower_limit)
        # lower == upper
        upper_limit = UpperClosedLimit(0)
        self.assertIsInstance(Interval(lower_limit, upper_limit), Interval)
        # lower > upper
        upper_limit = UpperOpenLimit(0)
        self.assertRaises(InvalidInterval, Interval, upper_limit, lower_limit)

    def test_hash(self):
        lower_limit = LowerClosedLimit(0)
        upper_limit = UpperClosedLimit(1)
        # closed interval
        ival = Interval(lower_limit, upper_limit)
        self.assertEqual(hash(ival), hash((lower_limit, upper_limit)))
        # upper open interval
        ival = Interval(lower_limit=lower_limit)
        self.assertEqual(hash(ival),
                         hash((lower_limit, UpperInfiniteLimit())))
        # lower open interval
        ival = Interval(upper_limit=upper_limit)
        self.assertEqual(hash(ival),
                         hash((LowerInfiniteLimit(), upper_limit)))
        # unbounded interval
        ival = Interval()
        self.assertEqual(hash(ival),
                         hash((LowerInfiniteLimit(), UpperInfiniteLimit())))

    def test_comparison(self):
        uu = LowerClosedInterval(1000)
        uma = OpenBoundedInterval(20, 30)
        umo = OpenBoundedInterval(15, 25)
        m = ClosedInterval(10, 20)
        s1 = ClosedInterval(15, 20)
        s2 = ClosedInterval(10, 15)
        s3 = ClosedInterval(15, 15)
        lmo = OpenBoundedInterval(-5, 15)
        lma = OpenBoundedInterval(-50, 10)
        lu = UpperClosedInterval(-1000)
        # eq
        self.assertEqual(m, m)
        self.assertEqual(uma, uma)
        self.assertEqual(uu, uu)
        self.assertEqual(lu, lu)
        self.assertTrue(m != uu)
        self.assertTrue(m != uma)
        self.assertTrue(m != umo)
        self.assertTrue(m != s1)
        self.assertTrue(m != s2)
        self.assertTrue(m != s3)
        self.assertTrue(m != lmo)
        self.assertTrue(m != lma)
        self.assertTrue(m != lu)
        # lt
        self.assertTrue(lu < lma < lmo < s2 < m < s3 < s1 < umo < uma < uu)
        # gt
        self.assertTrue(uu > uma > umo > s1 > s3 > m > s2 > lmo > lma > lu)

    def test_set_ops(self):
        uu = LowerClosedInterval(1000)
        uma = OpenBoundedInterval(20, 30)
        umo = OpenBoundedInterval(15, 25)
        m = ClosedInterval(10, 20)
        s1 = ClosedInterval(15, 20)
        s2 = ClosedInterval(10, 15)
        s3 = ClosedInterval(15, 15)
        lmo = OpenBoundedInterval(-5, 15)
        lma = OpenBoundedInterval(-50, 10)
        lu = UpperClosedInterval(-1000)
        # test is_subset
        self.assertTrue(s1.is_subset(m))
        self.assertTrue(s2.is_subset(m))
        self.assertTrue(s3.is_subset(m))
        self.assertTrue(not m.is_subset(s1))
        self.assertTrue(not m.is_subset(s2))
        self.assertTrue(not m.is_subset(s3))
        self.assertTrue(s3.is_subset(s2))
        self.assertTrue(not s3.is_subset(umo))
        self.assertTrue(not s3.is_subset(lmo))
        # test __sub__
        self.assertRaises(InvalidInterval, Interval.__sub__, m, m)
        self.assertRaises(InvalidInterval, Interval.__sub__, m, s3)
        self.assertRaises(InvalidInterval, Interval.__sub__, s3, m)
        self.assertEqual(m - s1, Interval(LowerClosedLimit(10),
                                          UpperOpenLimit(15)))
        self.assertEqual(m - s2, Interval(LowerOpenLimit(15),
                                          UpperClosedLimit(20)))
        self.assertEqual(s2 - s1, Interval(LowerClosedLimit(10),
                                           UpperOpenLimit(15)))
        self.assertEqual(s1 - s2, Interval(LowerOpenLimit(15),
                                           UpperClosedLimit(20)))
        self.assertEqual(m - umo, Interval(LowerClosedLimit(10),
                                           UpperClosedLimit(15)))
        self.assertEqual(m - lmo, Interval(LowerClosedLimit(15),
                                           UpperClosedLimit(20)))
        self.assertEqual(m - uma, m)
        self.assertEqual(m - lma, m)
        self.assertEqual(m - uu, m)
        self.assertEqual(m - lu, m)
        # test union
        self.assertEqual(m | s1, m)
        self.assertEqual(m | s2, m)
        self.assertEqual(m | s3, m)
        self.assertEqual(m | umo, Interval(LowerClosedLimit(10),
                                           UpperOpenLimit(25)))
        self.assertEqual(m | lmo, Interval(LowerOpenLimit(-5),
                                           UpperClosedLimit(20)))
        self.assertEqual(m | uma, Interval(LowerClosedLimit(10),
                                           UpperOpenLimit(30)))
        self.assertEqual(m | lma, Interval(LowerOpenLimit(-50),
                                           UpperClosedLimit(20)))
        self.assertRaises(InvalidInterval, Interval.__or__, m, uu)
        self.assertRaises(InvalidInterval, Interval.__or__, m, lu)
        # test intersection
        self.assertEqual(m & s1, s1)
        self.assertEqual(m & s2, s2)
        self.assertEqual(m & s3, s3)
        self.assertEqual(m & umo, Interval(LowerOpenLimit(15),
                                           UpperClosedLimit(20)))
        self.assertEqual(m & lmo, Interval(LowerClosedLimit(10),
                                           UpperOpenLimit(15)))
        self.assertRaises(InvalidInterval, Interval.__and__, m, uma)
        self.assertRaises(InvalidInterval, Interval.__and__, m, lma)
        self.assertRaises(InvalidInterval, Interval.__and__, m, uu)
        self.assertRaises(InvalidInterval, Interval.__and__, m, lu)


class IntervalChainTests(unittest.TestCase):

    def test_constructor(self):
        limits = (0, 10, 50, 300)
        # lower_closed=True, add_lower_inf=False, add_upper_inf=True
        ic = IntervalChain(limits)
        self.assertEqual(len(ic), len(limits))
        self.assertEqual(ic.limits, limits)
        self.assertFalse(ic.is_lower_infinite())
        self.assertTrue(ic.is_upper_infinite())
        self.assertTrue(ic[1].lower_limit.is_closed())
        self.assertEqual(ic.total_interval, LowerClosedInterval(limits[0]))
        ivals = ic._ivals
        for idx in range(len(ivals) - 1):
            self.assertTrue(ic[idx].is_adjacent(ic[idx + 1]))
        # lower_closed=False, add_lower_inf=False, add_upper_inf=True
        ic = IntervalChain(limits, lower_closed=False)
        self.assertEqual(len(ic), len(limits))
        self.assertEqual(ic.limits, limits)
        self.assertFalse(ic.is_lower_infinite())
        self.assertTrue(ic.is_upper_infinite())
        self.assertTrue(ic[1].lower_limit.is_open())
        self.assertEqual(ic.total_interval, LowerOpenInterval(limits[0]))
        ivals = ic._ivals
        for idx in range(len(ivals) - 1):
            self.assertTrue(ic[idx].is_adjacent(ic[idx + 1]))
        # lower_closed=True, add_lower_inf=True, add_upper_inf=True
        ic = IntervalChain(limits, add_lower_inf=True)
        self.assertEqual(len(ic), len(limits) + 1)
        self.assertEqual(ic.limits, limits)
        self.assertTrue(ic.is_lower_infinite())
        self.assertTrue(ic.is_upper_infinite())
        self.assertEqual(ic.total_interval, Interval())
        ivals = ic._ivals
        for idx in range(len(ivals) - 1):
            self.assertTrue(ic[idx].is_adjacent(ic[idx + 1]))
        # lower_closed=True, add_lower_inf=True, add_upper_inf=False
        ic = IntervalChain(limits, add_lower_inf=True, add_upper_inf=False)
        self.assertEqual(len(ic), len(limits))
        self.assertEqual(ic.limits, limits)
        self.assertTrue(ic.is_lower_infinite())
        self.assertFalse(ic.is_upper_infinite())
        self.assertEqual(ic.total_interval, UpperOpenInterval(limits[-1]))
        ivals = ic._ivals
        for idx in range(len(ivals) - 1):
            self.assertTrue(ic[idx].is_adjacent(ic[idx + 1]))
        # lower_closed=True, add_lower_inf=False, add_upper_inf=False
        ic = IntervalChain(limits, add_lower_inf=False, add_upper_inf=False)
        self.assertEqual(len(ic), len(limits) - 1)
        self.assertEqual(ic.limits, limits)
        self.assertFalse(ic.is_lower_infinite())
        self.assertFalse(ic.is_upper_infinite())
        self.assertEqual(ic.total_interval,
                         ChainableInterval(limits[0], limits[-1]))
        ivals = ic._ivals
        for idx in range(len(ivals) - 1):
            self.assertTrue(ic[idx].is_adjacent(ic[idx + 1]))

    def test_if_immutable(self):
        limits = [0, 10, 50, 300]
        ic = IntervalChain(limits)
        self.assertRaises(TypeError, delitem, ic, 0)
        self.assertRaises(TypeError, setitem, ic, 0, 5)
        self.assertEqual(ic.limits, tuple(limits))
        del limits[0]
        self.assertNotEqual(ic.limits, tuple(limits))

    def test_copy(self):
        limits = (0, 10, 50, 300)
        ic = IntervalChain(limits)
        self.assertIs(copy(ic), ic)
        self.assertIsNot(deepcopy(ic), ic)

    def test_sequence(self):
        limits = [0, 10, 50, 300]
        ic = IntervalChain(limits)
        self.assertEqual(len(ic), len(limits))
        for idx in range(len(ic)):
            self.assertEqual(ic[idx].lower_limit.value, limits[idx])
        for idx, ival in enumerate(ic):
            self.assertEqual(ival.lower_limit.value, limits[idx])
        for idx, ival in enumerate(ic):
            self.assertEqual(idx, ic.index(ival))
        for ival in ic:
            self.assertTrue(ival in ic)
            self.assertEqual(ic.count(ival), 1)
        self.assertRaises(IndexError, ic.__getitem__, 6)
        self.assertFalse(LowerOpenInterval(0) in ic)
        idx = len(limits)
        for ival in reversed(ic):
            idx -= 1
            self.assertEqual(ival.lower_limit.value, limits[idx])

    def test_map2idx(self):
        # upper end infinite
        ic = IntervalChain(range(0, 1001, 5))
        self.assertRaises(ValueError, ic.map2idx, -4)
        self.assertEqual(ic.map2idx(2), 0)
        self.assertEqual(ic.map2idx(200), 40)
        self.assertEqual(ic.map2idx(2133), 200)
        # lower end infinite
        ic = IntervalChain(range(0, 1001, 5),
                           add_lower_inf=True, add_upper_inf=False)
        self.assertEqual(ic.map2idx(-4), 0)
        self.assertEqual(ic.map2idx(2), 1)
        self.assertEqual(ic.map2idx(200), 41)
        self.assertRaises(ValueError, ic.map2idx, 1003)
        # both ends infinite
        ic = IntervalChain(range(0, 1001, 5), add_lower_inf=True)
        self.assertEqual(ic.map2idx(-4), 0)
        self.assertEqual(ic.map2idx(2), 1)
        self.assertEqual(ic.map2idx(200), 41)
        self.assertEqual(ic.map2idx(2133), 201)
        # no end inifinite
        ic = IntervalChain(range(0, 1001, 5), add_upper_inf=False)
        self.assertRaises(ValueError, ic.map2idx, -4)
        self.assertEqual(ic.map2idx(328), 65)
        self.assertRaises(ValueError, ic.map2idx, 1003)

    def test_eq(self):
        limits = (0, 10, 50, 300)
        ic1 = IntervalChain(limits)
        self.assertEqual(ic1, ic1)
        ic2 = IntervalChain(limits)
        self.assertEqual(ic1, ic2)
        ic2 = IntervalChain(limits, lower_closed=False)
        self.assertNotEqual(ic1, ic2)
        ic2 = IntervalChain(limits, add_lower_inf=True)
        self.assertNotEqual(ic1, ic2)
        ic2 = IntervalChain(limits, add_upper_inf=False)
        self.assertNotEqual(ic1, ic2)

    def test_repr(self):
        limits = (0, 10, 50, 300)
        # lower_closed=True, add_lower_inf=False, add_upper_inf=True
        ic = IntervalChain(limits)
        r = repr(ic)
        self.assertEqual(ic, eval(r))
        # lower_closed=False, add_lower_inf=False, add_upper_inf=True
        ic = IntervalChain(limits, lower_closed=False)
        r = repr(ic)
        self.assertEqual(ic, eval(r))
        # lower_closed=True, add_lower_inf=True, add_upper_inf=True
        ic = IntervalChain(limits, add_lower_inf=True)
        r = repr(ic)
        self.assertEqual(ic, eval(r))
        # lower_closed=True, add_lower_inf=True, add_upper_inf=False
        ic = IntervalChain(limits, add_lower_inf=True, add_upper_inf=False)
        r = repr(ic)
        self.assertEqual(ic, eval(r))
        # lower_closed=True, add_lower_inf=False, add_upper_inf=False
        ic = IntervalChain(limits, add_lower_inf=False, add_upper_inf=False)
        r = repr(ic)
        self.assertEqual(ic, eval(r))


class IntervalMappingTests(unittest.TestCase):

    def test_constructor(self):
        limits = (0, 10, 50, 300)
        ic = IntervalChain(limits)
        vals = ('alarming', 'low', 'medium', 'high')
        items = tuple(zip(ic, vals))
        im = IntervalMapping(ic, vals)
        self.assertIsInstance(im._keys, IntervalChain)
        self.assertEqual(im._keys, ic)
        self.assertEqual(im._vals, tuple(vals))
        self.assertEqual(tuple(im.keys()), tuple(ic))
        self.assertEqual(tuple(im.values()), tuple(vals))
        self.assertEqual(tuple(im.items()), items)
        # alternate arg
        im = IntervalMapping(list(zip(limits, vals)))
        self.assertIsInstance(im._keys, IntervalChain)
        self.assertEqual(im._keys, ic)
        self.assertEqual(im._vals, tuple(vals))
        self.assertEqual(tuple(im.keys()), tuple(ic))
        self.assertEqual(tuple(im.values()), tuple(vals))
        self.assertEqual(tuple(im.items()), items)
        # non-infinite limits
        limits = ('a', 'k', 'p', 'z')
        ic = IntervalChain(limits, add_lower_inf=False, add_upper_inf=False)
        vals = [1, 2, 3]
        items = tuple(zip(ic, vals))
        im = IntervalMapping(ic, vals)
        self.assertIsInstance(im._keys, IntervalChain)
        self.assertEqual(im._keys, ic)
        self.assertEqual(im._vals, tuple(vals))
        self.assertEqual(tuple(im.keys()), tuple(ic))
        self.assertEqual(tuple(im.values()), tuple(vals))
        self.assertEqual(tuple(im.items()), items)
        # check wrong args
        self.assertRaises(TypeError, IntervalMapping)
        self.assertRaises(TypeError, IntervalMapping, 5)
        self.assertRaises(TypeError, IntervalMapping, (5, 7, 20))
        self.assertRaises(TypeError, IntervalMapping, 'abc')
        self.assertRaises(TypeError, IntervalMapping, ic)
        self.assertRaises(TypeError, IntervalMapping, ic, vals, 'abc')
        self.assertRaises(InvalidInterval, IntervalMapping,
                          [(5, 'a'), (1, 'b')])

    def test_if_immutable(self):
        limits = (0, 10, 50, 300)
        ic = IntervalChain(limits)
        vals = ['alarming', 'low', 'medium', 'high']
        im = IntervalMapping(ic, vals)
        self.assertRaises(TypeError, delitem, im, ic[0])
        self.assertRaises(TypeError, setitem, im, ic[0], 'x')
        self.assertEqual(im._vals, tuple(vals))
        del vals[0]
        self.assertNotEqual(im._vals, tuple(vals))

    def test_copy(self):
        limits = (0, 10, 50, 300)
        ic = IntervalChain(limits)
        vals = ('a', 'b', 'c', 'd')
        im = IntervalMapping(ic, vals)
        self.assertIs(copy(im), im)
        self.assertIsNot(deepcopy(im), im)

    def test_mapping(self):
        limits = (0, 10, 50, 300)
        ic = IntervalChain(limits)
        vals = ['alarming', 'low', 'medium', 'high']
        im = IntervalMapping(ic, vals)
        self.assertEqual(len(im), len(vals))
        for key in im:
            self.assertEqual(im[key], vals[ic.index(key)])
        self.assertRaises(KeyError, im.__getitem__, LowerOpenInterval(0))
        self.assertFalse(LowerOpenInterval(0) in im)
        for ival in ic:
            self.assertTrue(ival in im)

    def test_eq(self):
        limits = (0, 10, 50, 300)
        ic = IntervalChain(limits)
        vals = ('alarming', 'low', 'medium', 'high')
        im1 = IntervalMapping(ic, vals)
        self.assertEqual(im1, im1)
        im2 = IntervalMapping(ic, vals)
        self.assertEqual(im1, im2)
        # alternate arg
        tl = list(zip(limits, vals))
        im2 = IntervalMapping(tl)
        self.assertEqual(im1, im2)
        # dict holding same keys and values
        d = dict(tl)
        self.assertNotEqual(im2, d)

    def test_interval_mapping(self):
        limits = (0, 10, 50, 300)
        ic = IntervalChain(limits)
        vals = ('alarming', 'low', 'medium', 'high')
        im = IntervalMapping(ic, vals)
        self.assertEqual(im.map(5), 'alarming')
        self.assertEqual(im.map(10), 'low')
        self.assertEqual(im(500), 'high')
        self.assertRaises(KeyError, im.map, -4)
        limits = ('a', 'k', 'p', 'z')
        ic = IntervalChain(limits, add_lower_inf=False, add_upper_inf=False)
        vals = (1, 2, 3)
        im = IntervalMapping(ic, vals)
        self.assertEqual(im.map('a'), 1)
        self.assertEqual(im.map('j'), 1)
        self.assertEqual(im('y'), 3)
        self.assertRaises(KeyError, im.map, 'A')
        self.assertRaises(KeyError, im, 'z')


if __name__ == '__main__':
    unittest.main()
