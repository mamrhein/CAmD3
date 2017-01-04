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
from sys import maxsize
from pycomba.types.interval import (Inf, NegInf, Interval, InvalidInterval,
                                    LowerClosedInterval, UpperClosedInterval,
                                    LowerOpenInterval, UpperOpenInterval,
                                    ClosedInterval, OpenBoundedInterval,
                                    ChainableInterval, Limit, InfiniteLimit,
                                    LowerInfiniteLimit, UpperInfiniteLimit,
                                    LowerClosedLimit, LowerOpenLimit,
                                    UpperClosedLimit, UpperOpenLimit,
                                    IntervalChain, EmptyIntervalChain,
                                    IntervalMapping)


class InfinityTests(unittest.TestCase):

    def test_infinity_values(self):
        inf = Inf()
        neg_inf = NegInf()
        # do we have singletons?
        self.assertIs(inf, Inf())
        self.assertIs(neg_inf, NegInf())
        # there's nothing greater than Inf()
        self.assertTrue(inf == Inf())
        self.assertTrue(inf >= Inf())
        for val in (neg_inf, maxsize, 'zzz', object()):
            self.assertFalse(val >= inf)
        # there's nothing smaller than NegInf()
        self.assertTrue(neg_inf == NegInf())
        self.assertTrue(neg_inf <= NegInf())
        for val in (inf, maxsize, 'zzz', object()):
            self.assertFalse(val <= neg_inf)


class LimitTests(unittest.TestCase):

    def test_infinite_limits(self):
        self.assertRaises(AssertionError, InfiniteLimit, '')
        lower_inf = LowerInfiniteLimit()
        upper_inf = UpperInfiniteLimit()
        # infinite limits are singletons
        self.assertIs(lower_inf, InfiniteLimit(True))
        self.assertIs(upper_inf, InfiniteLimit(False))
        # infinite limits have 'Inf' values (which are singletons)
        self.assertIs(lower_inf.value, NegInf())
        self.assertIs(upper_inf.value, Inf())
        # infinite limits are always open
        self.assertFalse(lower_inf.is_closed())
        self.assertFalse(upper_inf.is_closed())
        # infinite limits have no adjacent limit
        self.assertIs(lower_inf.adjacent_limit(), None)
        self.assertIs(upper_inf.adjacent_limit(), None)
        # only NegInf() is smaller than LowerInfiniteLimit()
        self.assertTrue(NegInf() < lower_inf)
        self.assertTrue(NegInf() <= lower_inf)
        for val in (upper_inf, -maxsize, 'zzz', object()):
            self.assertFalse(val <= lower_inf)
        # only Inf() is greater than UpperInfiniteLimit()
        self.assertTrue(Inf() > upper_inf)
        self.assertTrue(Inf() >= upper_inf)
        for val in (lower_inf, maxsize, 'zzz', object()):
            self.assertFalse(val >= upper_inf)

    def test_limit_ops(self):
        lower_closed_limit = LowerClosedLimit(0)
        upper_closed_limit = UpperClosedLimit(0)
        lower_open_limit = LowerOpenLimit(0)
        upper_open_limit = UpperOpenLimit(0)
        # limits are immutable
        self.assertIs(copy(lower_closed_limit), lower_closed_limit)
        self.assertIs(deepcopy(lower_closed_limit), lower_closed_limit)
        # if values are equal: upper+open < closed < lower+open ...
        self.assertTrue(upper_open_limit < upper_closed_limit ==
                        lower_closed_limit < lower_open_limit)
        # ... otherwise limits compare like their values
        self.assertTrue(UpperOpenLimit(7) > UpperClosedLimit(6) >
                        LowerClosedLimit(5) > LowerOpenLimit(4))
        self.assertTrue(UpperOpenLimit('a') < UpperClosedLimit('b') <
                        LowerClosedLimit('c') < LowerOpenLimit('d'))
        # compare limits to values
        self.assertTrue(lower_closed_limit == 0)
        self.assertTrue(upper_closed_limit == 0)
        self.assertFalse(lower_closed_limit == '0')
        self.assertFalse(lower_open_limit == 0)
        self.assertFalse(upper_open_limit == 0)
        #self.assertRaises(TypeError, )
        # two limits are adjacent when they are not equal and there is no
        # value between them
        self.assertEqual(lower_closed_limit.adjacent_limit(),
                         upper_open_limit)
        self.assertEqual(upper_closed_limit.adjacent_limit(),
                         lower_open_limit)
        self.assertEqual(lower_open_limit.adjacent_limit(),
                         upper_closed_limit)
        self.assertEqual(upper_open_limit.adjacent_limit(),
                         lower_closed_limit)
        self.assertTrue(lower_closed_limit.is_adjacent(upper_open_limit))
        self.assertTrue(upper_open_limit.is_adjacent(lower_closed_limit))


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

    def test_properties(self):
        lower_limit = LowerClosedLimit(0)
        upper_limit = UpperClosedLimit(1)
        # closed interval
        ival = Interval(lower_limit, upper_limit)
        self.assertTrue(ival.is_lower_bounded())
        self.assertTrue(ival.is_upper_bounded())
        self.assertTrue(ival.is_bounded())
        self.assertFalse(ival.is_lower_unbounded())
        self.assertFalse(ival.is_upper_unbounded())
        self.assertFalse(ival.is_unbounded())
        self.assertTrue(ival.is_lower_closed())
        self.assertTrue(ival.is_upper_closed())
        self.assertTrue(ival.is_closed())
        self.assertFalse(ival.is_lower_open())
        self.assertFalse(ival.is_upper_open())
        self.assertFalse(ival.is_open())
        # upper open interval
        ival = Interval(lower_limit=lower_limit)
        self.assertTrue(ival.is_lower_bounded())
        self.assertFalse(ival.is_upper_bounded())
        self.assertFalse(ival.is_bounded())
        self.assertFalse(ival.is_lower_unbounded())
        self.assertTrue(ival.is_upper_unbounded())
        self.assertTrue(ival.is_unbounded())
        self.assertTrue(ival.is_lower_closed())
        self.assertFalse(ival.is_upper_closed())
        self.assertFalse(ival.is_closed())
        self.assertFalse(ival.is_lower_open())
        self.assertTrue(ival.is_upper_open())
        self.assertTrue(ival.is_open())
        # lower open interval
        ival = Interval(upper_limit=upper_limit)
        self.assertFalse(ival.is_lower_bounded())
        self.assertTrue(ival.is_upper_bounded())
        self.assertFalse(ival.is_bounded())
        self.assertTrue(ival.is_lower_unbounded())
        self.assertFalse(ival.is_upper_unbounded())
        self.assertTrue(ival.is_unbounded())
        self.assertFalse(ival.is_lower_closed())
        self.assertTrue(ival.is_upper_closed())
        self.assertFalse(ival.is_closed())
        self.assertTrue(ival.is_lower_open())
        self.assertFalse(ival.is_upper_open())
        self.assertTrue(ival.is_open())
        # unbounded interval
        ival = Interval()
        self.assertFalse(ival.is_lower_bounded())
        self.assertFalse(ival.is_upper_bounded())
        self.assertFalse(ival.is_bounded())
        self.assertTrue(ival.is_lower_unbounded())
        self.assertTrue(ival.is_upper_unbounded())
        self.assertTrue(ival.is_unbounded())
        self.assertFalse(ival.is_lower_closed())
        self.assertFalse(ival.is_upper_closed())
        self.assertFalse(ival.is_closed())
        self.assertTrue(ival.is_lower_open())
        self.assertTrue(ival.is_upper_open())
        self.assertTrue(ival.is_open())

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
        # le
        self.assertTrue(
            lu <= lma <= lmo <= s2 <= m <= s3 <= s1 <= umo <= uma <= uu)
        # gt
        self.assertTrue(uu > uma > umo > s1 > s3 > m > s2 > lmo > lma > lu)
        # ge
        self.assertTrue(
            uu >= uma >= umo >= s1 >= s3 >= m >= s2 >= lmo >= lma >= lu)

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

    def test_repr(self):
        lower_limit = LowerClosedLimit(0)
        upper_limit = UpperClosedLimit(1)
        # closed interval
        ival = Interval(lower_limit, upper_limit)
        self.assertEqual(ival, eval(repr(ival)))
        # upper open interval
        ival = Interval(lower_limit=lower_limit)
        self.assertEqual(ival, eval(repr(ival)))
        # lower open interval
        ival = Interval(upper_limit=upper_limit)
        self.assertEqual(ival, eval(repr(ival)))
        # unbounded interval
        ival = Interval()
        self.assertEqual(ival, eval(repr(ival)))


class IntervalChainTests(unittest.TestCase):

    def test_constructor(self):
        limits = (0, 10, 50, 300)
        min_n_ivals = len(limits) - 1
        for add_lower_inf in (True, False):
            for add_upper_inf in (True, False):
                n_ivals = min_n_ivals + (int(add_lower_inf) +
                                         int(add_upper_inf))
                for lower_closed in (True, False):
                    ic = IntervalChain(limits,
                                       lower_closed=lower_closed,
                                       add_lower_inf=add_lower_inf,
                                       add_upper_inf=add_upper_inf)
                    self.assertEqual(ic.limits, limits)
                    self.assertEqual(len(ic), n_ivals)
                    self.assertEqual(ic.is_lower_infinite(), add_lower_inf)
                    self.assertEqual(ic.is_upper_infinite(), add_upper_inf)
                    self.assertEqual(ic[1].lower_limit.is_closed(),
                                     lower_closed)
                    if add_lower_inf:
                        lower_limit = LowerInfiniteLimit()
                    elif lower_closed:
                        lower_limit = LowerClosedLimit(limits[0])
                    else:
                        lower_limit = LowerOpenLimit(limits[0])
                    if add_upper_inf:
                        upper_limit = UpperInfiniteLimit()
                    elif lower_closed:
                        upper_limit = UpperOpenLimit(limits[-1])
                    else:
                        upper_limit = UpperClosedLimit(limits[-1])
                    self.assertEqual(ic.total_interval,
                                     Interval(lower_limit, upper_limit))
                    ivals = ic._ivals
                    for idx in range(len(ivals) - 1):
                        self.assertTrue(ic[idx].is_adjacent(ic[idx + 1]))
        # limits that do not define any interval:
        self.assertRaises(EmptyIntervalChain, IntervalChain, ())
        self.assertRaises(EmptyIntervalChain,
                          IntervalChain, (3,), add_upper_inf=False)

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
        # two tuples given
        limits = (0, 10, 50, 300)
        vals = ('alarming', 'low', 'medium', 'high')
        im = IntervalMapping(limits, vals)
        self.assertIsInstance(im._keys, IntervalChain)
        self.assertEqual(tuple(im.keys()), tuple(IntervalChain(limits)))
        self.assertEqual(tuple(im.values()), vals)
        # check wrong args
        self.assertRaises(TypeError, IntervalMapping)
        self.assertRaises(TypeError, IntervalMapping, 5)
        self.assertRaises(TypeError, IntervalMapping, (5, 7, 20))
        self.assertRaises(AssertionError, IntervalMapping, (5, 7), ('a',))
        self.assertRaises(AssertionError, IntervalMapping, (), ())
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
