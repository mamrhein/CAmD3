# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        test_specification
# Purpose:     Test driver for module specification.
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


"""Test driver for module specification."""


import unittest
import operator
from itertools import combinations
from pycomba.infrastructure import (Attribute, ValueObject, implementer,
                                    register_utility, get_utility)
from pycomba.infrastructure.component import Component
from pycomba.infrastructure.specification.specification import (
    Specification, NegatedSpecification, CompositeSpecification,
    IntervalSpecification, IntervalSpecificationFactory,
    ValueSpecification, ValueSpecificationFactory)
from pycomba.types.interval import (Interval, ClosedInterval,
                                    LowerOpenInterval, UpperOpenInterval,
                                    IntervalChain, InvalidInterval)


class ITestObj1(Component):

    a = Attribute()
    b = Attribute()


@implementer(ITestObj1)
class TestObj1(ValueObject):

    a = Attribute()
    b = Attribute()

    def __init__(self, a=1, b=2):
        self.a = a
        self.b = b


class ITestObj2(ITestObj1):

    ab = Attribute(doc='a * b')


@implementer(ITestObj2)
class TestObj2(ValueObject):

    a = Attribute()
    b = Attribute()
    ab = Attribute(doc='a * b')

    def __init__(self, a=1, b=2):
        self.a = a
        self.b = b
        self.ab = a * b


class TestObj3(Component):

    a = Attribute()

    def __init__(self, a):
        self.a = a


def setUpModule():
    # register needed components
    register_utility(ValueSpecification, ValueSpecificationFactory)
    register_utility(IntervalSpecification, IntervalSpecificationFactory)


class TestFactories(unittest.TestCase):

    def setUp(self):
        self.value_spec_factory = get_utility(ValueSpecificationFactory)
        self.interval_spec_factory = get_utility(IntervalSpecificationFactory)

    def testValueSpecFactory(self):
        params = (ITestObj1, 'b', operator.eq, 2)
        spec = self.value_spec_factory(*params)
        self.assertTrue(isinstance(spec, Specification))
        self.assertTrue(spec.interface is ITestObj1)
        self.assertEqual(spec._params(), params)
        # nested attribute
        params = (ITestObj1, 'b.x.y', operator.eq, 2)
        spec = self.value_spec_factory(*params)
        self.assertTrue(isinstance(spec, Specification))
        self.assertTrue(spec.interface is ITestObj1)
        self.assertEqual(spec._params(), params)

    def testIntervalSpecFactory(self):
        params = (ITestObj1, 'b', ClosedInterval(2, 7))
        spec = self.interval_spec_factory(*params)
        self.assertTrue(isinstance(spec, Specification))
        self.assertTrue(spec.interface is ITestObj1)
        self.assertEqual(spec._params(), params)
        spec = self.interval_spec_factory(ITestObj1, 'b', (2, 7))
        self.assertTrue(isinstance(spec, Specification))
        self.assertTrue(spec.interface is ITestObj1)
        self.assertEqual(spec._params(), params)
        # nested attribute
        params = (ITestObj1, 'b.xyz', ClosedInterval(2, 7))
        spec = self.interval_spec_factory(*params)
        self.assertTrue(isinstance(spec, Specification))
        self.assertTrue(spec.interface is ITestObj1)
        # wrong number of values
        self.assertRaises(ValueError, self.interval_spec_factory,
                          ITestObj1, 'b', (2, 7, 3))
        # wrong type of interval
        self.assertRaises(TypeError, self.interval_spec_factory,
                          ITestObj1, 'b', {2, 7})


class TestComposition(unittest.TestCase):

    def setUp(self):
        value_spec_factory = get_utility(ValueSpecificationFactory)
        self.vspec1 = value_spec_factory(ITestObj1, 'b', operator.eq, 2)
        self.vspec2 = value_spec_factory(ITestObj2, 'ab', operator.gt, 20)
        self.vspec3 = value_spec_factory(TestObj3, 'a', operator.eq, 2)
        interval_spec_factory = get_utility(IntervalSpecificationFactory)
        self.ispec1 = interval_spec_factory(ITestObj1, 'a',
                                            ClosedInterval(2, 7))
        self.ispec2 = interval_spec_factory(ITestObj2, 'ab', (-12, -7))

    def testCompositeSpec(self):
        for op in (operator.and_, operator.or_):
            cspec = op(self.vspec1, self.vspec2)
            self.assertTrue(isinstance(cspec, Specification))
            self.assertTrue(cspec.interface is ITestObj1)
        for op in (operator.and_, operator.or_):
            cspec = op(self.ispec1, self.vspec2)
            self.assertTrue(isinstance(cspec, Specification))
            self.assertTrue(cspec.interface is ITestObj1)
        for op in (operator.and_, operator.or_):
            cspec = op(self.ispec1, self.ispec2)
            self.assertTrue(isinstance(cspec, Specification))
            self.assertTrue(cspec.interface is ITestObj1)
        for op in (operator.and_, operator.or_):
            cspec = op(self.ispec2, self.vspec2)
            self.assertTrue(isinstance(cspec, Specification))
            self.assertTrue(cspec.interface is ITestObj2)
        for op in (operator.and_, operator.or_):
            cspec = CompositeSpecification(op, self.vspec1, self.vspec2,
                                           self.ispec1, self.ispec2)
            self.assertTrue(isinstance(cspec, Specification))
            self.assertTrue(cspec.interface is ITestObj1)
        # invalid operator
        self.assertRaises(AssertionError, CompositeSpecification,
                          operator.eq, self.vspec1, self.vspec2)
        # invalid numbers of specs
        self.assertRaises(AssertionError, CompositeSpecification,
                          operator.or_)
        self.assertRaises(AssertionError, CompositeSpecification,
                          operator.or_, self.vspec1)
        # invalid argument
        self.assertRaises(AssertionError, CompositeSpecification,
                          operator.or_, self.vspec1, self.vspec1, 'abc')
        # incompatible specs
        self.assertRaises(ValueError, CompositeSpecification,
                          operator.or_, self.vspec1, self.vspec3)


class TestNegation(unittest.TestCase):

    def setUp(self):
        self.value_spec_factory = get_utility(ValueSpecificationFactory)
        self.interval_spec_factory = get_utility(IntervalSpecificationFactory)

    def testValueSpec(self):
        for op1, op2 in [(operator.eq, operator.ne),
                         (operator.lt, operator.ge),
                         (operator.gt, operator.le),
                         (operator.is_, operator.is_not)]:
            spec1 = self.value_spec_factory(ITestObj1, 'a', op1, 1)
            spec2 = self.value_spec_factory(ITestObj1, 'a', op2, 1)
            neg_spec1 = ~spec1
            neg_spec2 = ~spec2
            self.assertTrue(isinstance(neg_spec1, Specification))
            self.assertTrue(neg_spec1.interface is spec1.interface)
            self.assertTrue(isinstance(neg_spec2, Specification))
            self.assertTrue(neg_spec2.interface is spec2.interface)
            self.assertEqual(spec1, neg_spec2)
            self.assertEqual(spec2, neg_spec1)
            self.assertEqual(spec1, ~neg_spec1)
            self.assertEqual(spec2, ~neg_spec2)
        # non-predefined operator:
        spec = self.value_spec_factory(ITestObj1, 'a', lambda x, y: x == y, 1)
        neg_spec = ~spec
        self.assertTrue(isinstance(neg_spec, Specification))
        self.assertTrue(neg_spec.interface is spec.interface)
        self.assertEqual(spec, ~neg_spec)

    def testIntervalSpec(self):
        spec = self.interval_spec_factory(ITestObj1, 'a', (1, 7))
        neg_spec = ~spec
        self.assertTrue(isinstance(neg_spec, Specification))
        self.assertTrue(neg_spec.interface is spec.interface)
        spec = self.interval_spec_factory(ITestObj2, 'ab',
                                          LowerOpenInterval(-12))
        neg_spec = ~spec
        self.assertTrue(isinstance(neg_spec, Specification))
        self.assertTrue(neg_spec.interface is spec.interface)
        spec = self.interval_spec_factory(ITestObj2, 'ab',
                                          UpperOpenInterval(-12))
        neg_spec = ~spec
        self.assertTrue(isinstance(neg_spec, Specification))
        self.assertTrue(neg_spec.interface is spec.interface)
        spec = self.interval_spec_factory(ITestObj1, 'a', Interval())
        self.assertRaises(InvalidInterval, operator.invert, spec)

    def testCompositeSpec(self):
        vspec1 = self.value_spec_factory(ITestObj1, 'b', operator.eq, 2)
        vspec2 = self.value_spec_factory(ITestObj2, 'ab', operator.gt, 20)
        ispec1 = self.interval_spec_factory(ITestObj1, 'a',
                                            ClosedInterval(2, 7))
        ispec2 = self.interval_spec_factory(ITestObj2, 'ab', (-12, -7))
        for op in (operator.and_, operator.or_):
            for spec1, spec2 in combinations((vspec1, vspec2,
                                              ispec1, ispec2), 2):
                spec = op(spec1, spec2)
                neg_spec = ~spec
                self.assertTrue(isinstance(neg_spec, Specification))
                self.assertTrue(neg_spec.interface is spec.interface)


class TestImmutable(unittest.TestCase):

    def setUp(self):
        self.value_spec_factory = get_utility(ValueSpecificationFactory)
        self.interval_spec_factory = get_utility(IntervalSpecificationFactory)

    def testImmutable(self):
        spec = self.value_spec_factory(ITestObj1, 'b', lambda x, y: x == y, 2)
        self.assertRaises(AttributeError, setattr, spec, 'interface', 'xx')
        self.assertRaises(AttributeError, delattr, spec, 'interface')
        self.assertRaises(AttributeError, setattr, spec, 'x', 'xx')
        spec = ~spec
        self.assertRaises(AttributeError, setattr, spec, 'interface', 'xx')
        self.assertRaises(AttributeError, delattr, spec, 'interface')
        self.assertRaises(AttributeError, setattr, spec, 'x', 'xx')
        spec = self.interval_spec_factory(ITestObj1, 'a', (1, 7))
        self.assertRaises(AttributeError, setattr, spec, 'interface', 'xx')
        self.assertRaises(AttributeError, delattr, spec, 'interface')
        self.assertRaises(AttributeError, setattr, spec, 'x', 'xx')
        spec = spec & self.value_spec_factory(ITestObj1, 'b', operator.eq, 2)
        self.assertRaises(AttributeError, setattr, spec, 'interface', 'xx')
        self.assertRaises(AttributeError, delattr, spec, 'interface')
        self.assertRaises(AttributeError, setattr, spec, 'x', 'xx')


class TestIsSatisfiedBy(unittest.TestCase):

    def setUp(self):
        self.value_spec_factory = get_utility(ValueSpecificationFactory)
        self.interval_spec_factory = get_utility(IntervalSpecificationFactory)

    def testValueSpec(self):
        val = 5
        tObj = TestObj1(b=val)
        for op1, op2 in [(operator.eq, operator.ne),
                         (operator.lt, operator.ge),
                         (operator.gt, operator.le),
                         (operator.is_, operator.is_not)]:
            spec1 = self.value_spec_factory(ITestObj1, 'b', op1, val)
            spec2 = self.value_spec_factory(ITestObj1, 'b', op2, val)
            self.assertEqual(spec1.is_satisfied_by(tObj), op1(tObj.b, val))
            self.assertFalse(spec1.is_satisfied_by(tObj) and
                             spec2.is_satisfied_by(tObj))
            spec1 = self.value_spec_factory(ITestObj1, 'b', op1, -val)
            spec2 = self.value_spec_factory(ITestObj1, 'b', op2, -val)
            self.assertEqual(spec1.is_satisfied_by(tObj), op1(tObj.b, -val))
            self.assertFalse(spec1.is_satisfied_by(tObj) and
                             spec2.is_satisfied_by(tObj))
        # compare instance of subclass
        tObj = TestObj2(b=val)
        spec = self.value_spec_factory(ITestObj1, 'b', operator.eq, val)
        self.assertTrue(spec.is_satisfied_by(tObj))
        spec = self.value_spec_factory(ITestObj1, 'b', operator.lt, val)
        self.assertFalse(spec.is_satisfied_by(tObj))
        # object with incompatible interface never satisfies spec
        tObj = TestObj3(val)
        for op in (operator.eq, operator.ne, operator.ge, operator.gt):
            spec = self.value_spec_factory(ITestObj1, 'b', op, val)
            self.assertFalse(spec.is_satisfied_by(tObj))

    def testIntervalSpec(self):
        a, b = 5, 7
        ab = a * b
        tObj = TestObj2(a, b)
        for ival in [ClosedInterval(0, 10), ClosedInterval(20, 50),
                     LowerOpenInterval(-12), LowerOpenInterval(72),
                     UpperOpenInterval(-12), UpperOpenInterval(72)]:
            spec = self.interval_spec_factory(ITestObj2, 'ab', ival)
            self.assertEqual(spec.is_satisfied_by(tObj), ab in ival)
        limits = [3, ab]
        for lower_closed in (True, False):
            for add_lower_inf in (True, False):
                for add_upper_inf in (True, False):
                    ic = IntervalChain(limits, lower_closed=lower_closed,
                                       add_lower_inf=add_lower_inf,
                                       add_upper_inf=add_upper_inf)
                    for ival in ic:
                        spec = self.interval_spec_factory(ITestObj2, 'ab',
                                                          ival)
                        self.assertEqual(spec.is_satisfied_by(tObj),
                                         ab in ival)
        # compare instance of subclass
        val = 23
        tObj = TestObj2(b=val)
        spec = self.interval_spec_factory(ITestObj1, 'b', (20, 50))
        self.assertTrue(spec.is_satisfied_by(tObj))
        spec = self.interval_spec_factory(ITestObj1, 'b', (3, 17))
        self.assertFalse(spec.is_satisfied_by(tObj))
        # object with incompatible interface never satisfies spec
        tObj = TestObj3(val)
        for min_max in ((0, 5), (20, 25), (67, 70)):
            spec = self.interval_spec_factory(ITestObj1, 'b', min_max)
            self.assertFalse(spec.is_satisfied_by(tObj))

    def testCompositeSpec(self):
        a, b = 5, 7
        ab = a * b
        tObj = TestObj2(a, b)
        vspec1 = self.value_spec_factory(ITestObj1, 'b', operator.eq, b)
        vspec2 = self.value_spec_factory(ITestObj2, 'ab', operator.lt, ab)
        ispec = self.interval_spec_factory(ITestObj1, 'a', (1, 7))
        cspec = CompositeSpecification(operator.and_, vspec1, vspec2, ispec)
        self.assertFalse(cspec.is_satisfied_by(tObj))
        cspec = CompositeSpecification(operator.or_, vspec1, vspec2, ispec)
        self.assertTrue(cspec.is_satisfied_by(tObj))
        cspec = (vspec1 & vspec2) & ispec
        self.assertFalse(cspec.is_satisfied_by(tObj))
        cspec = (vspec1 & vspec2) | ispec
        self.assertTrue(cspec.is_satisfied_by(tObj))
        cspec = (vspec1 | vspec2) & ~ispec
        self.assertFalse(cspec.is_satisfied_by(tObj))
        cspec = (~vspec1 | vspec2) | ~ispec
        self.assertFalse(cspec.is_satisfied_by(tObj))
        cspec = (vspec1 & ~vspec2) & ispec
        self.assertTrue(cspec.is_satisfied_by(tObj))

    def testNestedAttribute(self):
        a, b = 5, 7
        ab = a * b
        tObj = TestObj1(a=3, b=TestObj2(a, b))
        vspec = self.value_spec_factory(ITestObj1, 'b.ab',
                                        lambda x, y: x == y, ab)
        self.assertTrue(vspec.is_satisfied_by(tObj))
        vspec = ~self.value_spec_factory(ITestObj1, 'b.ab',
                                         lambda x, y: x != y, ab)
        self.assertTrue(vspec.is_satisfied_by(tObj))
        ispec = self.interval_spec_factory(ITestObj1, 'b.a', (1, 7))
        self.assertTrue(ispec.is_satisfied_by(tObj))
        cspec = vspec & ispec
        self.assertTrue(cspec.is_satisfied_by(tObj))
        # undefined nested attribute => result is False
        vspec = self.value_spec_factory(ITestObj1, 'b.x', operator.eq, ab)
        self.assertFalse(vspec.is_satisfied_by(tObj))
        ispec = self.interval_spec_factory(ITestObj1, 'b.x', (1, 7))
        self.assertFalse(ispec.is_satisfied_by(tObj))


class TestRepr(unittest.TestCase):

    def setUp(self):
        self.value_spec_factory = get_utility(ValueSpecificationFactory)
        self.interval_spec_factory = get_utility(IntervalSpecificationFactory)

    def testRepr(self):

        def op(x, y):
            return x == y

        vspec = self.value_spec_factory(ITestObj2, 'a', op, 1)
        self.assertEqual(repr(vspec), '<ITestObj2 x: x.a op 1>')
        self.assertEqual(repr(~vspec), '<ITestObj2 x: not (x.a op 1)>')
        vspec = self.value_spec_factory(ITestObj2, 'a', operator.eq, 1)
        self.assertEqual(repr(vspec), '<ITestObj2 x: x.a eq 1>')
        ispec = self.interval_spec_factory(ITestObj2, 'a', (0, 6))
        self.assertEqual(repr(ispec), '<ITestObj2 x: x.a in [0 .. 6]>')
        cspec = ispec & vspec
        self.assertEqual(repr(cspec),
                         '<ITestObj2 x: all(x.a in [0 .. 6], x.a eq 1)>')


class TestEqualityAndHash(unittest.TestCase):

    def setUp(self):
        self.value_spec_factory = get_utility(ValueSpecificationFactory)
        self.interval_spec_factory = get_utility(IntervalSpecificationFactory)

    def test_eq_and_hash(self):

        def op(x, y):
            return x == y

        vspec1 = self.value_spec_factory(ITestObj2, 'a', op, 1)
        vspec2 = self.value_spec_factory(ITestObj2, 'a', op, 1)
        vspec3 = self.value_spec_factory(ITestObj2, 'a', operator.eq, 1)
        self.assertEqual(vspec1, vspec2)
        self.assertEqual(hash(vspec1), hash(vspec2))
        self.assertNotEqual(vspec1, vspec3)
        self.assertNotEqual(hash(vspec1), hash(vspec3))
        negvspec1 = NegatedSpecification(vspec1)
        negvspec2 = NegatedSpecification(vspec2)
        negvspec3 = NegatedSpecification(vspec3)
        self.assertEqual(negvspec1, negvspec2)
        self.assertEqual(hash(negvspec1), hash(negvspec2))
        self.assertNotEqual(negvspec1, negvspec3)
        self.assertNotEqual(hash(negvspec1), hash(negvspec3))
        self.assertNotEqual(vspec1, negvspec1)
        self.assertNotEqual(hash(vspec1), hash(negvspec1))
        ispec1 = self.interval_spec_factory(ITestObj2, 'a', (0, 6))
        ispec2 = self.interval_spec_factory(ITestObj2, 'a', (0, 6))
        ispec3 = self.interval_spec_factory(ITestObj2, 'a', (0, 5))
        self.assertEqual(ispec1, ispec2)
        self.assertEqual(hash(ispec1), hash(ispec2))
        self.assertNotEqual(ispec1, ispec3)
        self.assertNotEqual(hash(ispec1), hash(ispec3))
        self.assertNotEqual(vspec1, ispec1)
        self.assertNotEqual(hash(vspec1), hash(ispec1))
        cspec1 = ispec1 & vspec1
        cspec2 = ispec2 & vspec2
        cspec3 = ispec3 & vspec3
        self.assertEqual(cspec1, cspec2)
        self.assertEqual(hash(cspec1), hash(cspec2))
        self.assertNotEqual(cspec1, cspec3)
        self.assertNotEqual(hash(cspec1), hash(cspec3))
        self.assertNotEqual(vspec1, cspec1)
        self.assertNotEqual(hash(vspec1), hash(cspec1))
