#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_component
# Purpose:     Test driver for module component
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2014 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

from abc import ABC
from numbers import Number
from typing import Tuple
import unittest
from uuid import uuid1

from pycomba.infrastructure.component import (
    Attribute, Component, ComponentLookupError, Immutable, implementer,
    UniqueIdentifier)
from pycomba.infrastructure.component.component import _ABCSet, ComponentMeta


DFLT_NAMESPACE = ('__module__', '__qualname__', '__doc__')


class TestComp1(Component):
    """TestComp1"""


class TestComp2(Component):
    """TestComp2"""

    attr1 = Attribute()
    attr2 = Attribute()

    def meth(self):
        pass

    attr3 = Attribute()

    @property
    def prop(self):
        pass


@implementer(TestComp1, TestComp2)
class TestImpl(Component):

    def __init__(self):
        pass


class TestComp1Factory:

    def __call__(self, i: Number) -> TestComp1:
        return TestImpl()


def Number2TestComp1(i: Number) -> TestComp1:
    return TestImpl()


def Str2TestComp2(s: str) -> TestComp2:
    return TestImpl()


@implementer(TestComp1)
class TestABC(ABC):
    pass


class TestComp3(Component):
    """TestComp3"""

    def __init_subclass__(subcls, **kwds):
        try:
            param = kwds.pop('param')
        except KeyError:
            pass
        else:
            subcls.param = param


class TestImpl3(TestComp3, param='P'):
    pass


class TestComp4(Component, Immutable):
    """TestComp4"""


class TestComp5(TestComp4):
    """TestComp5"""

    a = Attribute()
    b = Attribute()


class TestComp6(TestComp5):
    """TestComp6"""

    c = Attribute()

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c


def Obj2TestComp6(obj: object) -> TestComp6:
    return TestComp6(obj, None, None)


def Tuple2TestComp6(tpl: Tuple[int, int, str]) -> TestComp6:
    return TestComp6(*tpl)


class TestComp7(TestComp6):
    """TestComp7"""


class ABCSetTest(unittest.TestCase):

    def testAdd(self):
        cls_list = (ABC, Immutable, TestComp4, Component)
        self.assertEqual(_ABCSet(cls_list), _ABCSet({ABC, TestComp4}))
        cls_list = (int, object, Number, float)
        self.assertEqual(_ABCSet(cls_list), _ABCSet({int, float}))


class ComponentMetaTest(unittest.TestCase):

    def test_constructor(self):
        # name of descriptors
        for name in ('attr1', 'attr2', 'attr3'):
            self.assertEqual(getattr(getattr(TestComp2, name, None),
                                     'name', None), name)
        # __slots__ forced?
        self.assertEqual(getattr(TestComp4, '__slots__', None), ())
        self.assertEqual(getattr(TestComp5, '__slots__', None), ('_a', '_b'))
        self.assertEqual(getattr(TestComp6, '__slots__', None), ('_c',))
        self.assertRaises(TypeError, ComponentMeta, 'Test',
                          (TestImpl, TestComp4), {})

    def test_init_subclass(self):
        # init_subclass turned into a class method?
        meth = TestComp3.__init_subclass__
        self.assertTrue(getattr(meth, '__self__', None) is TestComp3)
        # __init_subclass called?
        self.assertEqual(getattr(TestImpl3, 'param', None), 'P')

    def test_attr_names(self):
        self.assertEqual(TestComp2.attr_names, ('attr1', 'attr2', 'attr3'))
        self.assertEqual(TestComp2.all_attr_names,
                         ('attr1', 'attr2', 'attr3'))
        self.assertEqual(TestImpl.attr_names, ())
        self.assertEqual(TestImpl.all_attr_names, ())
        self.assertEqual(TestComp6.attr_names, ('c',))
        self.assertEqual(TestComp6.all_attr_names, ('a', 'b', 'c'))

    def test_implementer(self):
        self.assertTrue(issubclass(TestImpl, TestComp1))
        self.assertTrue(issubclass(TestImpl, TestComp2))
        self.assertEqual(TestImpl.__virtual_bases__, {TestComp1, TestComp2})
        self.assertTrue(issubclass(TestABC, TestComp1))

    def test_adaptation(self):
        # wrong component
        self.assertRaises(AssertionError, TestComp2.add_adapter,
                          TestComp1Factory())
        self.assertRaises(AssertionError, TestComp2.add_adapter,
                          Tuple2TestComp6)
        # wrong number of args
        func = lambda x, y: TestComp2()
        func.__annotations__ = {'return': TestComp2, 'x': int, 'y': int}
        self.assertRaises(AssertionError, TestComp2.add_adapter, func)
        # variable number of args
        func = lambda *args: TestComp2()
        func.__annotations__ = {'return': TestComp2, 'args': int}
        self.assertRaises(AssertionError, TestComp2.add_adapter, func)
        # register some adapters
        fct = TestComp1Factory()
        TestComp1.add_adapter(fct)
        self.assertIn(Number, TestComp1.__adapters__)
        self.assertIn(fct, TestComp1.__adapters__[Number])
        TestComp1.add_adapter(Number2TestComp1)
        self.assertIn(Number2TestComp1, TestComp1.__adapters__[Number])
        TestComp1.add_adapter(Number2TestComp1)
        self.assertEqual(len(TestComp1.__adapters__[Number]), 2)
        TestComp2.add_adapter(Str2TestComp2)
        self.assertIn(str, TestComp2.__adapters__)
        self.assertIn(Str2TestComp2, TestComp2.__adapters__[str])
        TestComp6.add_adapter(Tuple2TestComp6)
        adapter = TestComp6.add_adapter(Obj2TestComp6)
        self.assertEqual(adapter, Obj2TestComp6)
        # retrieve adapters
        self.assertEqual(TestComp1.get_adapter(5), fct)
        self.assertEqual(TestComp1.get_adapter(5.0), fct)
        self.assertRaises(ComponentLookupError, TestComp1.get_adapter, 'x')
        self.assertEqual(TestComp2.get_adapter('abc'), Str2TestComp2)
        self.assertRaises(ComponentLookupError, TestComp2.get_adapter, 3)
        self.assertEqual(TestComp6.get_adapter((3, 1, 'x')), Tuple2TestComp6)
        self.assertEqual(TestComp6.get_adapter([3, 1, 'x']), Obj2TestComp6)
        self.assertEqual(TestComp6.get_adapter(TestComp6(3, 1, 'x')),
                         Obj2TestComp6)
        # adapt objects
        self.assertIsInstance(TestComp1.adapt(5), TestComp1)
        self.assertIsInstance(TestComp1[5.0], TestComp1)
        self.assertIsInstance(TestComp2.adapt('x'), TestComp2)
        t1 = TestComp6.adapt((5, 17, 'abc'))
        self.assertIsInstance(t1, TestComp6)
        self.assertEqual((t1.a, t1.b, t1.c), (5, 17, 'abc'))
        t2 = TestComp6.adapt(fct)
        self.assertIsInstance(t2, TestComp6)
        self.assertIs(t2.a, fct)
        self.assertRaises(TypeError, TestComp7.adapt, t2)
        t3 = TestComp6(4, 9, 'y')
        for ct in (TestComp6, TestComp5, TestComp4):
            self.assertIs(ct.adapt(t3), t3)


class UniqueIdentifierTest(unittest.TestCase):

    def test_adapt(self):
        obj = object()
        self.assertRaises(TypeError, UniqueIdentifier.adapt, obj)
        uid = uuid1()
        self.assertIs(UniqueIdentifier[uid], uid)
        obj = type('Obj', (), {})()
        obj.id = 5
        self.assertRaises(TypeError, UniqueIdentifier.adapt, obj)
        obj.id = uid
        self.assertIs(UniqueIdentifier[obj], uid)


if __name__ == '__main__':
    unittest.main()
