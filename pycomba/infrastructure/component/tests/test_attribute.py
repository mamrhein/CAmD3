#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_attribute
# Purpose:     Test driver for module attribute
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2014 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

import unittest
from pycomba.infrastructure.component.attribute import Attribute, _NODEFAULT
from pycomba.infrastructure.component.constraints import (is_number,
                                                          non_negative,
                                                          between)
from pycomba.infrastructure.component.immutable import immutable


# helper to create class with attribute on the fly
def create_cls(cls_name, attr_dict):
    for name, attr in attr_dict.items():
        attr.__set_name__(name)
    return type(str(cls_name), (), attr_dict)


class AttributeTest(unittest.TestCase):

    def test_constructor(self):
        a = Attribute()
        self.assertTrue(a.immutable is False)
        self.assertTrue(a.default is _NODEFAULT)
        self.assertTrue(a.converter is None)
        self.assertTrue(a.constraints is None)
        self.assertEqual(a._bound_constraints, ())
        self.assertTrue(a.__doc__ is None)
        self.assertRaises(AttributeError, getattr, a, 'name')
        a = Attribute(immutable=True, default=5, converter=str,
                      constraints=is_number, doc='doc')
        a.__set_name__('a')
        self.assertTrue(a.immutable is True)
        self.assertEqual(a.default, 5)
        self.assertTrue(a.converter is str)
        self.assertTrue(a.constraints is is_number)
        self.assertTrue(type(a._bound_constraints) is tuple)
        self.assertTrue(all(callable(c) for c in a._bound_constraints))
        self.assertEqual(a.__doc__, 'doc')
        self.assertEqual(a.name, 'a')

    def test_access(self):
        a1 = Attribute()
        a2 = Attribute(default=1)
        a3 = Attribute(immutable=True)
        Test = create_cls('Test', {'x': a1, 'y': a2, 'z': a3})
        t1 = Test()
        self.assertRaises(AttributeError, getattr, t1, 'x')
        t1.x = 7
        self.assertEqual(t1.x, 7)
        self.assertEqual(t1.y, 1)
        t1.y = 5
        self.assertEqual(t1.y, 5)
        self.assertRaises(AttributeError, getattr, t1, 'z')
        t1.z = 7
        self.assertEqual(t1.z, 7)
        self.assertRaises(AttributeError, setattr, t1, 'z', 9)
        self.assertRaises(AttributeError, delattr, t1, 'z')
        t2 = Test()
        self.assertRaises(AttributeError, getattr, t2, 'x')
        t2.x = 7
        self.assertEqual(t2.x, 7)
        self.assertEqual(t2.y, 1)
        t2.y = 5
        self.assertEqual(t2.y, 5)
        self.assertRaises(AttributeError, getattr, t2, 'z')
        t2.z = 7
        self.assertEqual(t2.z, 7)
        self.assertRaises(AttributeError, setattr, t2, 'z', 9)
        self.assertRaises(AttributeError, delattr, t2, 'z')
        # immutable object
        a1 = Attribute()
        a2 = Attribute(default=1)
        a3 = Attribute(immutable=True)
        Immu = immutable(create_cls('Immu', {'x': a1, 'y': a2, 'z': a3}))
        im1 = Immu()
        im1.x = 'a'
        self.assertEqual(im1.x, 'a')
        self.assertEqual(im1.y, 1)
        im1.y = 'b'
        self.assertEqual(im1.y, 'b')
        self.assertRaises(AttributeError, getattr, im1, 'z')
        im1.z = 'c'
        self.assertEqual(im1.z, 'c')
        for attr in ('x', 'y', 'z'):
            self.assertRaises(AttributeError, setattr, im1, attr, 3)
            self.assertRaises(AttributeError, delattr, im1, attr)

    def test_default(self):
        double_x = lambda t: 2 * t.x
        a1 = Attribute(default=17)
        a2 = Attribute(default=double_x)
        Test = create_cls('Test', {'x': a1, 'y': a2})
        t = Test()
        self.assertEqual(t.x, 17)
        self.assertEqual(t.y, 34)
        t.x = 4
        self.assertEqual(t.x, 4)
        self.assertEqual(t.y, 8)
        t.y = 3
        self.assertEqual(t.y, 3)
        del t.y
        self.assertEqual(t.y, 8)

    def test_converter(self):
        a = Attribute(converter=str)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = 5
        self.assertEqual(t.x, '5')
        t.x = int
        self.assertEqual(t.x, str(int))
        a = Attribute(converter=int)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = 5
        self.assertEqual(t.x, 5)
        t.x = '5'
        self.assertEqual(t.x, 5)
        self.assertRaises(ValueError, setattr, t, 'x', 'a')

    def test_constraints(self):
        # single constraint
        a = Attribute(constraints=is_number)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = 5
        self.assertEqual(t.x, 5)
        self.assertRaises(ValueError, setattr, t, 'x', 'a')
        # several constraints
        a = Attribute(constraints=(is_number, non_negative, between(1, 7)))
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = 5
        self.assertEqual(t.x, 5)
        self.assertRaises(ValueError, setattr, t, 'x', 'a')
        self.assertRaises(ValueError, setattr, t, 'x', -3)
        self.assertRaises(ValueError, setattr, t, 'x', 9)


if __name__ == '__main__':
    unittest.main()
