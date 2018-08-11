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


"""Test driver for module attribute"""


from abc import ABC
from operator import delitem, setitem
import unittest

from camd3.infrastructure.component.attribute import (
    AbstractAttribute, Attribute, MultiValueAttribute,
    QualifiedMultiValueAttribute, _NODEFAULT, is_identifier)
from camd3.infrastructure.component.constraints import (
    is_number, non_negative, between)
from camd3.infrastructure.component.immutable import immutable


class HelperTest(unittest.TestCase):

    def test_is_identifier(self):
        self.assertTrue(is_identifier('_a_5'))
        self.assertFalse(is_identifier('3abc'))
        self.assertFalse(is_identifier('def'))
        self.assertFalse(is_identifier(7))


# helper to create class with attribute on the fly
def create_cls(cls_name, attr_dict, bases=(ABC,)):              # noqa: D103
    for name, attr in attr_dict.items():
        attr.__set_name__(None, name)
    return type(str(cls_name), bases, attr_dict)


class AbstractAttributeTest(unittest.TestCase):

    def test_constructor(self):
        a = AbstractAttribute()
        self.assertTrue(a.immutable is False)
        self.assertIsNone(a.__doc__)
        a = AbstractAttribute(immutable=True, doc='doc')
        a.__set_name__(None, 'a')
        self.assertEqual(a.name, 'a')
        self.assertTrue(a.immutable is True)
        self.assertEqual(a.__doc__, 'doc')
        # no positional args
        self.assertRaises(TypeError, AbstractAttribute, True)

    def test_being_abstract(self):
        a = AbstractAttribute()
        Test = create_cls('Test', {'x': a})
        self.assertRaises(TypeError, Test)


class AttributeTest(unittest.TestCase):

    def test_constructor(self):
        a = Attribute()
        self.assertTrue(a.immutable is False)
        self.assertTrue(a.default is _NODEFAULT)
        self.assertTrue(a.converter is None)
        self.assertTrue(a.constraints is None)
        self.assertEqual(a._bound_constraints, ())
        self.assertIsNone(a.__doc__)
        self.assertEqual(a.name, '<unnamed>')
        a = Attribute(immutable=True, default='5', converter=int,
                      constraints=is_number, doc='doc')
        a.__set_name__(None, 'a')
        self.assertEqual(a.name, 'a')
        self.assertTrue(a.immutable is True)
        self.assertEqual(a.default, 5)
        self.assertTrue(a.converter is int)
        self.assertTrue(a.constraints is is_number)
        self.assertTrue(type(a._bound_constraints) is tuple)
        self.assertTrue(all(callable(c) for c in a._bound_constraints))
        self.assertEqual(a.__doc__, 'doc')
        # default must be compatible to converter and must pass constraints
        self.assertRaises(TypeError, Attribute, converter=int,
                          default=object())
        self.assertRaises(ValueError, Attribute, converter=int, default='a')
        self.assertRaises(ValueError, Attribute,
                          constraints=(is_number, non_negative), default='a')
        self.assertRaises(ValueError, Attribute,
                          constraints=(is_number, non_negative), default=-7)
        # immutable must instance of bool
        self.assertRaises(AssertionError, Attribute, immutable='T')
        # converter must be callable
        self.assertRaises(AssertionError, Attribute, converter='x')
        # constaints must be a single callable or an iterable of callables
        self.assertRaises(AssertionError, Attribute, constraints=5)
        self.assertRaises(AssertionError, Attribute, constraints=(5, 'a'))
        # no positional args
        self.assertRaises(TypeError, Attribute, True)

    def test_name(self):
        a = Attribute()
        self.assertRaises(ValueError, a.__set_name__, None, '9ab')
        a.__set_name__(None, 'a')
        self.assertEqual(a._priv_member, '_a')
        self.assertIsNone(a.__set_name__(None, 'a'))
        self.assertRaises(AttributeError, a.__set_name__, None, 'b')
        a = Attribute()
        a.__set_name__(None, '_a')
        self.assertEqual(a._priv_member, '_a_')

    def test_access(self):
        a1 = Attribute()
        a2 = Attribute(default=1)
        a3 = Attribute(immutable=True)
        Test = create_cls('Test', {'x': a1, 'y': a2, 'z': a3})
        t1 = Test()
        self.assertRaises(AttributeError, getattr, t1, 'x')
        t1.x = 7
        self.assertEqual(t1.x, 7)
        del t1.x
        self.assertRaises(AttributeError, getattr, t1, 'x')
        self.assertIsNone(delattr(t1, 'x'))
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
        del t2.x
        self.assertRaises(AttributeError, getattr, t2, 'x')
        self.assertIsNone(delattr(t2, 'x'))
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
        self.assertRaises(TypeError, setattr, t, 'x', object())

    def test_constraints(self):
        # single constraint
        a = Attribute(constraints=is_number)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = 5
        self.assertEqual(t.x, 5)
        self.assertRaises(ValueError, setattr, t, 'x', 'a')
        # several constraints
        eq5 = lambda value: value == 5
        a = Attribute(constraints=(is_number, non_negative, between(1, 7),
                                   eq5))
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = 5
        self.assertEqual(t.x, 5)
        self.assertRaises(ValueError, setattr, t, 'x', 'a')
        self.assertRaises(ValueError, setattr, t, 'x', -3)
        self.assertRaises(ValueError, setattr, t, 'x', 9)
        self.assertRaises(ValueError, setattr, t, 'x', 2)


class MultiValueAttributeTest(unittest.TestCase):

    def test_constructor(self):
        a = MultiValueAttribute()
        self.assertTrue(a.immutable is False)
        self.assertTrue(a.default is _NODEFAULT)
        self.assertTrue(a.converter is None)
        self.assertTrue(a.constraints is None)
        self.assertEqual(a._bound_constraints, ())
        self.assertIsNone(a.__doc__)
        self.assertEqual(a.name, '<unnamed>')
        a = MultiValueAttribute(immutable=True, default={'5'}, converter=int,
                                constraints=is_number, doc='doc')
        a.__set_name__(None, 'a')
        self.assertTrue(a.immutable is True)
        self.assertEqual(a.default, {5})
        self.assertTrue(a.converter is int)
        self.assertTrue(a.constraints is is_number)
        self.assertTrue(type(a._bound_constraints) is tuple)
        self.assertTrue(all(callable(c) for c in a._bound_constraints))
        self.assertEqual(a.__doc__, 'doc')
        self.assertEqual(a.name, 'a')
        # default must be iterable
        self.assertRaises(TypeError, MultiValueAttribute, default=3)
        # items in default must be compatible to converter and must pass
        # constraints
        self.assertRaises(TypeError, MultiValueAttribute, converter=int,
                          default=[object()])
        self.assertRaises(ValueError, MultiValueAttribute, converter=int,
                          default=['1', 'a'])
        self.assertRaises(ValueError, MultiValueAttribute,
                          constraints=(is_number, non_negative),
                          default=[5, 9, 'a'])
        self.assertRaises(ValueError, MultiValueAttribute,
                          constraints=(is_number, non_negative),
                          default=[2, 3, 19, -7])

    def test_repr(self):
        x = MultiValueAttribute(default={1})
        Test = create_cls('Test', {'x': x})
        t1 = Test()
        self.assertRegex(repr(t1.x), '<.*\.%s: \%s>' % (Test.x.name, t1.x))
        t1.x = {2, 7, 55}
        self.assertRegex(repr(t1.x), '<.*\.%s: \%s>' % (Test.x.name, t1.x))

    def test_access(self):
        a1 = MultiValueAttribute()
        a2 = MultiValueAttribute(default={1})
        a3 = MultiValueAttribute(immutable=True)
        Test = create_cls('Test', {'x': a1, 'y': a2, 'z': a3})
        t1 = Test()
        self.assertRaises(AttributeError, getattr, t1, 'x')
        t1.x = (7, 33, 33)
        self.assertEqual(t1.x, {7, 33})
        del t1.x
        self.assertRaises(AttributeError, getattr, t1, 'x')
        self.assertIsNone(delattr(t1, 'x'))
        self.assertEqual(t1.y, {1})
        t1.y = {5}
        self.assertEqual(t1.y, {5})
        self.assertRaises(AttributeError, getattr, t1, 'z')
        t1.z = [7]
        self.assertEqual(t1.z, {7})
        self.assertRaises(AttributeError, setattr, t1, 'z', {9})
        self.assertRaises(AttributeError, delattr, t1, 'z')
        t2 = Test()
        self.assertRaises(AttributeError, getattr, t2, 'x')
        t2.x = (7, 33, 33)
        self.assertEqual(t2.x, {7, 33})
        del t2.x
        self.assertRaises(AttributeError, getattr, t2, 'x')
        self.assertIsNone(delattr(t2, 'x'))
        self.assertEqual(t2.y, {1})
        t2.y = {5}
        self.assertEqual(t2.y, {5})
        self.assertRaises(AttributeError, getattr, t2, 'z')
        t2.z = [7]
        self.assertEqual(t2.z, {7})
        self.assertRaises(AttributeError, setattr, t2, 'z', {9})
        self.assertRaises(AttributeError, delattr, t2, 'z')
        # immutable object
        a1 = MultiValueAttribute()
        a2 = MultiValueAttribute(default={1})
        a3 = MultiValueAttribute(immutable=True)
        Immu = immutable(create_cls('Immu', {'x': a1, 'y': a2, 'z': a3}))
        im1 = Immu()
        im1.x = ('a',)
        self.assertEqual(im1.x, {'a'})
        self.assertEqual(im1.y, {1})
        im1.y = ('b',)
        self.assertEqual(im1.y, {'b'})
        self.assertRaises(AttributeError, getattr, im1, 'z')
        im1.z = {'a', 'b', 'c'}
        self.assertEqual(im1.z, {'a', 'b', 'c'})
        for attr in ('x', 'y', 'z'):
            self.assertRaises(AttributeError, setattr, im1, attr, {3})
            self.assertRaises(AttributeError, delattr, im1, attr)

    def test_modifier(self):
        a1 = MultiValueAttribute()
        a2 = MultiValueAttribute(immutable=True)
        Test = create_cls('Test', {'x': a1, 'y': a2})
        t1 = Test()
        t1.x = (7, 33, 33)
        t1.x.add(5)
        self.assertEqual(t1.x, {5, 7, 33})
        t1.x.add(7)
        self.assertEqual(t1.x, {5, 7, 33})
        t1.x.discard(17)
        self.assertEqual(t1.x, {5, 7, 33})
        t1.x.discard(7)
        self.assertEqual(t1.x, {5, 33})
        t1.x.remove(5)
        self.assertEqual(t1.x, {33})
        self.assertRaises(KeyError, t1.x.remove, 5)
        t1.x.clear()
        self.assertEqual(t1.x, set())
        t1.x.update((1, 2, 2))
        t1.x.update({7, 33})
        self.assertEqual(t1.x, {1, 2, 7, 33})
        i = t1.x.pop()
        self.assertEqual(t1.x, {1, 2, 7, 33} - {i})
        t1.x.add(i)
        self.assertEqual(t1.x, {1, 2, 7, 33})
        s = set(t1.x)
        o = {7, 18, 33, 90}
        t1.x |= o
        self.assertEqual(t1.x, s | o)
        t1.x = s
        t1.x.intersection_update(o)
        self.assertEqual(t1.x, s & o)
        t1.x = s
        t1.x &= o
        self.assertEqual(t1.x, s & o)
        t1.x = s
        t1.x.difference_update(o)
        self.assertEqual(t1.x, s - o)
        t1.x = s
        t1.x -= o
        self.assertEqual(t1.x, s - o)
        t1.x = s
        t1.x.symmetric_difference_update(o)
        self.assertEqual(t1.x, s.symmetric_difference(o))
        # can't modify immutable attribute
        t1.y = {7}
        self.assertRaises(AttributeError, t1.y.add, 2)
        self.assertRaises(AttributeError, t1.y.discard, 8)
        self.assertRaises(AttributeError, t1.y.clear)
        self.assertRaises(AttributeError, t1.y.pop)
        self.assertRaises(AttributeError, t1.y.remove, 8)
        self.assertRaises(AttributeError, t1.y.update, (2, 9))
        self.assertRaises(AttributeError, t1.y.__ior__, {2, 9})
        self.assertRaises(AttributeError, t1.y.intersection_update, {2, 9})
        self.assertRaises(AttributeError, t1.y.__iand__, {2, 9})
        self.assertRaises(AttributeError, t1.y.difference_update, {2, 9})
        self.assertRaises(AttributeError, t1.y.__isub__, {2, 9})
        self.assertRaises(AttributeError,
                          t1.y.symmetric_difference_update, {2, 9})

    def test_default(self):
        double_x = lambda t: {2 * i for i in t.x}
        a1 = MultiValueAttribute(default={17})
        a2 = MultiValueAttribute(default=double_x)
        Test = create_cls('Test', {'x': a1, 'y': a2})
        t = Test()
        self.assertEqual(t.x, {17})
        self.assertEqual(t.y, {34})
        t.x = {4, 70}
        self.assertEqual(t.x, {4, 70})
        self.assertEqual(t.y, {8, 140})
        del t.x         # reset to default
        self.assertEqual(t.x, {17})
        self.assertEqual(t.y, {34})
        t.x.add(7)
        self.assertEqual(t.x, {7, 17})
        self.assertEqual(t.y, {14, 34})
        t.y = {3}
        self.assertEqual(t.y, {3})
        del t.x         # reset to default
        self.assertEqual(t.y, {3})
        del t.y         # reset to default
        self.assertEqual(t.x, {17})
        self.assertEqual(t.y, {34})
        t.x.discard(17)
        self.assertEqual(t.x, set())
        del t.x         # reset to default
        t.x.pop()
        self.assertEqual(t.x, set())
        del t.x         # reset to default
        t.x.clear()
        self.assertEqual(t.x, set())
        del t.x         # reset to default
        t.x.remove(17)
        self.assertEqual(t.x, set())
        del t.x         # reset to default
        t.x.update((2, 9))
        self.assertEqual(t.x, {2, 9, 17})
        del t.x         # reset to default
        t.x |= {2, 9}
        self.assertEqual(t.x, {2, 9, 17})
        del t.x         # reset to default
        t.x.intersection_update({2, 9})
        self.assertEqual(t.x, set())
        del t.x         # reset to default
        t.x &= {2, 9}
        self.assertEqual(t.x, set())
        del t.x         # reset to default
        t.x.difference_update({2, 9})
        self.assertEqual(t.x, {17})
        del t.x         # reset to default
        t.x -= {17}
        self.assertEqual(t.x, set())
        del t.x         # reset to default
        t.x.symmetric_difference_update({2, 9, 17})
        self.assertEqual(t.x, {2, 9})
        self.assertEqual(t.y, {4, 18})
        # callable default also linked to instance
        self.assertIs(t.y._instance, t.x._instance)
        # modifying default does fix the attribute value
        t.y.add(2)
        self.assertEqual(t.y, {2, 4, 18})
        t.x = set()
        self.assertEqual(t.y, {2, 4, 18})
        # deleting the attribute value restores the default
        del t.y
        self.assertEqual(t.y, set())

    def test_converter(self):
        a = MultiValueAttribute(converter=str)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = {5, 7, 'abc'}
        self.assertEqual(t.x, {'5', '7', 'abc'})
        t.x = [int]
        self.assertEqual(t.x, {str(int)})
        a = MultiValueAttribute(converter=int)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = {5, '-9'}
        self.assertEqual(t.x, {-9, 5})
        self.assertRaises(ValueError, setattr, t, 'x', ('17', '12.090'))
        self.assertRaises(TypeError, setattr, t, 'x', [object()])

    def test_constraints(self):
        # single constraint
        a = MultiValueAttribute(constraints=is_number)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = {5}
        self.assertEqual(t.x, {5})
        self.assertRaises(ValueError, setattr, t, 'x', {'a'})
        # several constraints
        eq5 = lambda value: value == 5
        a = MultiValueAttribute(constraints=(is_number, non_negative,
                                             between(1, 7), eq5))
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = {5}
        self.assertEqual(t.x, {5})
        self.assertRaises(ValueError, setattr, t, 'x', {'a'})
        self.assertRaises(ValueError, setattr, t, 'x', {-3})
        self.assertRaises(ValueError, setattr, t, 'x', {9})
        self.assertRaises(ValueError, setattr, t, 'x', {2})


class QualifiedMultiValueAttributeTest(unittest.TestCase):

    def test_constructor(self):
        a = QualifiedMultiValueAttribute(int)
        self.assertTrue(a.immutable is False)
        self.assertTrue(a.default is _NODEFAULT)
        self.assertTrue(a.converter is None)
        self.assertTrue(a.constraints is None)
        self.assertEqual(a._bound_constraints, ())
        self.assertIsNone(a.__doc__)
        self.assertEqual(a.name, '<unnamed>')
        a = QualifiedMultiValueAttribute(int, immutable=True,
                                         default={1: '5'}, converter=int,
                                         constraints=is_number, doc='doc')
        a.__set_name__(None, 'a')
        self.assertTrue(a.immutable is True)
        self.assertEqual(a.default, {1: 5})
        self.assertTrue(a.converter is int)
        self.assertTrue(a.constraints is is_number)
        self.assertTrue(type(a._bound_constraints) is tuple)
        self.assertTrue(all(callable(c) for c in a._bound_constraints))
        self.assertEqual(a.__doc__, 'doc')
        self.assertEqual(a.name, 'a')
        # default must be a Mapping or an Iterable
        self.assertRaises(TypeError, QualifiedMultiValueAttribute, int,
                          default=3)
        # keys in default must be of given key_type
        self.assertRaises(TypeError, QualifiedMultiValueAttribute, int,
                          default={'a': 5})
        # values in default must be compatible to converter and must pass
        # constraints
        self.assertRaises(TypeError, QualifiedMultiValueAttribute, int,
                          converter=int, default={1: object()})
        self.assertRaises(ValueError, QualifiedMultiValueAttribute, int,
                          converter=int, default={1: '1', 2: 'a'})
        self.assertRaises(ValueError, QualifiedMultiValueAttribute, int,
                          constraints=(is_number, non_negative),
                          default={1: 5, 2: 9, 3: 'a'})
        self.assertRaises(ValueError, QualifiedMultiValueAttribute, int,
                          constraints=(is_number, non_negative),
                          default={1: 2, 2: 3, 3: 19, 4: -7})

    def test_repr(self):
        x = QualifiedMultiValueAttribute(object, default={1: 'a'})
        Test = create_cls('Test', {'x': x})
        t1 = Test()
        self.assertRegex(repr(t1.x), '<.*\.%s: \%s>' % (Test.x.name, t1.x))
        t1.x = {'a': 2, 'b': 7, 'c': 55}
        self.assertRegex(repr(t1.x), '<.*\.%s: \%s>' % (Test.x.name, t1.x))

    def test_access(self):
        a1 = QualifiedMultiValueAttribute(object)
        a2 = QualifiedMultiValueAttribute(str, default={'a': 1})
        a3 = QualifiedMultiValueAttribute(str, immutable=True)
        Test = create_cls('Test', {'x': a1, 'y': a2, 'z': a3})
        t1 = Test()
        self.assertRaises(AttributeError, getattr, t1, 'x')
        o = object()
        t1.x = {o: 33}
        self.assertEqual(t1.x, {o: 33})
        del t1.x
        self.assertRaises(AttributeError, getattr, t1, 'x')
        self.assertIsNone(delattr(t1, 'x'))
        self.assertEqual(t1.y, {'a': 1})
        t1.y = {'a': 5}
        self.assertEqual(t1.y, {'a': 5})
        self.assertRaises(AttributeError, getattr, t1, 'z')
        t1.z = {'a': 7}
        self.assertEqual(t1.z, {'a': 7})
        self.assertRaises(AttributeError, setattr, t1, 'z', {'a': 9})
        self.assertRaises(AttributeError, delattr, t1, 'z')
        t2 = Test()
        self.assertRaises(AttributeError, getattr, t2, 'x')
        t2.x = {o: 33}
        self.assertEqual(t2.x, {o: 33})
        del t2.x
        self.assertRaises(AttributeError, getattr, t2, 'x')
        self.assertIsNone(delattr(t2, 'x'))
        self.assertEqual(t2.y, {'a': 1})
        t2.y = {'a': 5}
        self.assertEqual(t2.y, {'a': 5})
        self.assertRaises(AttributeError, getattr, t2, 'z')
        t2.z = {'a': 7}
        self.assertEqual(t2.z, {'a': 7})
        self.assertRaises(AttributeError, setattr, t2, 'z', {'a': 9})
        self.assertRaises(AttributeError, delattr, t2, 'z')
        # immutable object
        a1 = QualifiedMultiValueAttribute(object)
        a2 = QualifiedMultiValueAttribute(str, default={'a': 1})
        a3 = QualifiedMultiValueAttribute(str, immutable=True)
        Immu = immutable(create_cls('Immu', {'x': a1, 'y': a2, 'z': a3}))
        im1 = Immu()
        im1.x = ((o, 'a'), ('x', 'X'), (7, 17))
        self.assertEqual(im1.x, {o: 'a', 'x': 'X', 7: 17})
        self.assertEqual(im1.y, {'a': 1})
        im1.y = [('b', 3)]
        self.assertEqual(im1.y, {'b': 3})
        self.assertRaises(AttributeError, getattr, im1, 'z')
        im1.z = {'a': 1, 'b': 2, 'c': 3}
        self.assertEqual(im1.z, {'a': 1, 'b': 2, 'c': 3})
        for attr in ('x', 'y', 'z'):
            self.assertRaises(AttributeError, setattr, im1, attr, {'a': 3})
            self.assertRaises(AttributeError, delattr, im1, attr)

    def test_modifier(self):
        a1 = QualifiedMultiValueAttribute(object)
        a2 = QualifiedMultiValueAttribute(str, immutable=True)
        Test = create_cls('Test', {'x': a1, 'y': a2})
        t = Test()
        t.x = {1: 'a', 2: 'b', 3: 'c'}
        t.x[4] = 'd'
        self.assertEqual(t.x, {1: 'a', 2: 'b', 3: 'c', 4: 'd'})
        del t.x[2]
        self.assertEqual(t.x, {1: 'a', 3: 'c', 4: 'd'})
        v = t.x.pop(3)
        self.assertEqual(v, 'c')
        self.assertEqual(t.x, {1: 'a', 4: 'd'})
        d = dict(t.x)
        v = t.x.pop(3, 'x')
        self.assertEqual(v, 'x')
        self.assertEqual(t.x, d)
        k, v = t.x.popitem()
        d.pop(k)
        self.assertEqual(t.x, d)
        t.x.update({1: 'a', 3: 'c', 4: 'd'}, two='b', more=42)
        self.assertEqual(t.x,
                         {1: 'a', 3: 'c', 4: 'd', 'two': 'b', 'more': 42})
        d = dict(t.x)
        t.x.clear()
        self.assertEqual(t.x, {})
        v = t.x.setdefault(3, 'c')
        self.assertEqual(v, 'c')
        self.assertEqual(t.x, {3: 'c'})
        t.x.update(d.items())
        self.assertEqual(t.x, d)
        # can't modify immutable attribute
        t.y = {'a': 7}
        self.assertRaises(AttributeError, setitem, t.y, 'a', 2)
        self.assertRaises(AttributeError, delitem, t.y, 'a')
        self.assertRaises(AttributeError, t.y.pop, 'a')
        self.assertRaises(AttributeError, t.y.popitem)
        self.assertRaises(AttributeError, t.y.clear)
        self.assertRaises(AttributeError, t.y.update, {})
        self.assertRaises(AttributeError, t.y.setdefault, 'a')

    def test_default(self):
        double_x = lambda t: {(k, 2 * v) for k, v in t.x.items()}
        a1 = QualifiedMultiValueAttribute(str, default={'a': 17})
        a2 = QualifiedMultiValueAttribute(str, default=double_x)
        Test = create_cls('Test', {'x': a1, 'y': a2})
        t = Test()
        self.assertEqual(t.x, {'a': 17})
        self.assertEqual(t.y, {'a': 34})
        t.x = {'a': 4, 'b': 70}
        self.assertEqual(t.x, {'a': 4, 'b': 70})
        self.assertEqual(t.y, {'a': 8, 'b': 140})
        t.y = {'a': 3}
        self.assertEqual(t.y, {'a': 3})
        del t.y
        self.assertEqual(t.y, {'a': 8, 'b': 140})
        # callable default also linked to instance
        self.assertIs(t.y._instance, t.x._instance)
        # modifying default does fix the attribute value
        t.y['c'] = 9
        self.assertEqual(t.y, {'a': 8, 'b': 140, 'c': 9})
        t.x = {}
        self.assertEqual(t.y, {'a': 8, 'b': 140, 'c': 9})
        # deleting the attribute value restores the default
        del t.y
        self.assertEqual(t.y, {})

    def test_converter(self):
        a = QualifiedMultiValueAttribute(str, converter=str)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = [('a', 5), ('b', 7), ('c', 'abc')]
        self.assertEqual(t.x, {'a': '5', 'b': '7', 'c': 'abc'})
        t.x = [('x', int)]
        self.assertEqual(t.x, {'x': str(int)})
        a = QualifiedMultiValueAttribute(str, converter=int)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = {'a': 5, 'b': '-9'}
        self.assertEqual(t.x, {'a': 5, 'b': -9})
        self.assertRaises(ValueError, setattr, t, 'x', (('a', '17'),
                                                        ('b', '12.090')))
        self.assertRaises(TypeError, setattr, t, 'x', [('x', object())])

    def test_constraints(self):
        # single constraint
        a = QualifiedMultiValueAttribute(str, constraints=is_number)
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = {'a': 5}
        self.assertEqual(t.x, {'a': 5})
        self.assertRaises(ValueError, setattr, t, 'x', {'a': 'a'})
        # several constraints
        eq5 = lambda value: value == 5
        a = QualifiedMultiValueAttribute(str,
                                         constraints=(is_number, non_negative,
                                                      between(1, 7), eq5))
        Test = create_cls('Test', {'x': a})
        t = Test()
        t.x = {'a': 5}
        self.assertEqual(t.x, {'a': 5})
        self.assertRaises(ValueError, setattr, t, 'x', {'a': 'a'})
        self.assertRaises(ValueError, setattr, t, 'x', {'a': -3})
        self.assertRaises(ValueError, setattr, t, 'x', {'a': 9})
        self.assertRaises(ValueError, setattr, t, 'x', {'a': 2})


if __name__ == '__main__':
    unittest.main()
