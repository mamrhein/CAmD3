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
import unittest
from pycomba.infrastructure.component import (
    Attribute, Component, Immutable, implementer)
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


class ABCSetTest(unittest.TestCase):

    def testAdd(self):
        cls_list = (ABC, Immutable, TestComp4, Component)
        self.assertEqual(_ABCSet(cls_list), _ABCSet({ABC, TestComp4}))
        cls_list = (int, object, Number, float)
        self.assertEqual(_ABCSet(cls_list), _ABCSet({int, float}))


class ComponentMetaTest(unittest.TestCase):

    def test_constructor(self):
        # definition order
        self.assertEqual(getattr(TestComp1, '__definition_order__', None),
                         DFLT_NAMESPACE)
        self.assertEqual(getattr(TestComp2, '__definition_order__', None),
                         DFLT_NAMESPACE + ('attr1', 'attr2', 'meth', 'attr3',
                                           'prop'))
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
        self.assertEqual(TestComp2.all_attr_names, ('attr1', 'attr2', 'attr3'))
        self.assertEqual(TestImpl.attr_names, ())
        self.assertEqual(TestImpl.all_attr_names, ())
        self.assertEqual(TestComp6.attr_names, ('c',))
        self.assertEqual(TestComp6.all_attr_names, ('a', 'b', 'c'))

    def test_implementer(self):
        self.assertTrue(issubclass(TestImpl, TestComp1))
        self.assertTrue(issubclass(TestImpl, TestComp2))


if __name__ == '__main__':
    unittest.main()
