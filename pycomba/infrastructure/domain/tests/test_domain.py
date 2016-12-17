#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_domain
# Purpose:     Test driver for module domain
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

from copy import copy
import unittest
from uuid import UUID
from pycomba.infrastructure import register_factory
from pycomba.infrastructure import Attribute
from pycomba.infrastructure.domain import (Entity,
                                           AggregateRoot,
                                           ValueObject,
                                           uuid_generator,
                                           UUIDGenerator)


# --- Entity ---

class TestEntity1(Entity):

    id = Attribute(immutable=True,)

    def __init__(self, id):
        self.id = id


class TestEntity2(Entity):

    id = Attribute(immutable=True,)

    def __init__(self, id):
        self.id = id


class EntityTest(unittest.TestCase):

    def test_constructor(self):
        for id in (1, 18, 'a', 'aa'):
            entity = TestEntity1(id)
            self.assertEqual(entity.id, id)

    def test_equality(self):
        for cls1 in (TestEntity1, TestEntity2):
            for id1 in (1, 18, 'a', object()):
                e1 = cls1(id1)
                for cls2 in (TestEntity1, TestEntity2):
                    for id2 in (1, 18, 'a', object()):
                        e2 = cls2(id2)
                        if cls1 is cls2 and id1 == id2:
                            self.assertEqual(e1, e2)
                            self.assertEqual(hash(e1), hash(e2))
                        else:
                            self.assertNotEqual(e1, e2)
                            self.assertNotEqual(hash(e1), hash(e2))


# --- AggregateRoot ---

class TestAggregate(AggregateRoot):

    def __init__(self, *args, **kwds):
        pass


class AggregateRootTest(unittest.TestCase):

    def setUp(self):
        # register UUID generator factory
        register_factory(uuid_generator)

    def test_constructor(self):
        nIds = 10
        dict_ = {}
        for id in range(nIds):
            entity = TestAggregate()
            self.assertTrue(isinstance(entity.id, UUID))
            dict_[entity.id] = entity
        self.assertEqual(len(dict_), nIds)


# --- ValueObject ---

class VO1(ValueObject):

    x = Attribute()
    y = Attribute()

    def __init__(self, x=1, y=2):
        self.x = x
        self.y = y


class VO2(VO1):

    z = Attribute()

    def __init__(self, z=3):
        super(VO2, self).__init__()
        self.z = z


class VO3(ValueObject):

    s1 = Attribute()
    s2 = Attribute()

    def __init__(self, s1='abc', s2='xyz'):
        self.s1 = s1
        self.s2 = s2


class VO4(VO3):

    s3 = Attribute()
    s4 = Attribute()
    s5 = Attribute()

    def __init__(self, s3=1, s4=2, s5=3):
        super(VO4, self).__init__()
        self.s3 = s3
        self.s4 = s4
        self.s5 = s5


class VO5(ValueObject):

    v1 = Attribute()
    v4 = Attribute()
    a = Attribute()

    def __init__(self, a, x=7, s5=9):
        self.a = a
        self.v1 = VO1(x=x)
        self.v4 = VO4(s5=s5)


class VO6(VO2):

    def __getstate__(self):
        return (self.x, self.y)


class VO7(VO4):

    pass


class ValueObjectTest(unittest.TestCase):

    def test_attr_access(self):
        val1 = VO1()
        self.assertEqual((val1.x, val1.y), (1, 2))
        self.assertRaises(AttributeError, setattr, val1, 'x', 5)
        self.assertRaises(AttributeError, delattr, val1, 'x')
        self.assertRaises(AttributeError, setattr, val1, 'a', '')
        val2 = VO2(17)
        self.assertEqual((val2.x, val2.y), (1, 2))
        self.assertEqual(val2.z, 17)
        self.assertRaises(AttributeError, setattr, val2, 'z', 5)
        self.assertRaises(AttributeError, delattr, val2, 'z')
        self.assertRaises(AttributeError, setattr, val2, 'a', '')
        val3 = VO3()
        self.assertEqual((val3.s1, val3.s2), ('abc', 'xyz'))
        self.assertRaises(AttributeError, setattr, val3, 's2', 5)
        self.assertRaises(AttributeError, delattr, val3, 's2')
        self.assertRaises(AttributeError, setattr, val3, 'a', '')
        val4 = VO4(17)
        self.assertEqual((val4.s1, val4.s2), ('abc', 'xyz'))
        self.assertEqual((val4.s3, val4.s4, val4.s5), (17, 2, 3))
        self.assertRaises(AttributeError, setattr, val4, 's4', 5)
        self.assertRaises(AttributeError, delattr, val4, 's4')
        self.assertRaises(AttributeError, setattr, val4, 'a', '')
        val5 = VO5(8)
        self.assertEqual((val5.v1.x, val5.v1.y), (7, 2))
        self.assertEqual((val5.v4.s1, val5.v4.s2), ('abc', 'xyz'))
        self.assertEqual((val5.v4.s3, val5.v4.s4, val5.v4.s5), (1, 2, 9))
        self.assertEqual(val5.a, 8)
        self.assertRaises(AttributeError, setattr, val5.v4, 's4', 5)
        self.assertRaises(AttributeError, delattr, val5.v4, 's4')
        self.assertRaises(AttributeError, setattr, val5, 'a', '')

    def test_state(self):
        # __getstate__
        val = VO2(17)
        self.assertEqual(val.__getstate__(), (1, 2, 17))
        val = VO4()
        self.assertEqual(val.__getstate__(), ('abc', 'xyz', 1, 2, 3))
        val = VO5('', s5=34)
        self.assertEqual(val.__getstate__(), ('', VO1(x=7), VO4(s5=34)))
        # class with __getstate__:
        val = VO6()
        self.assertEqual(val.__getstate__(), (val.x, val.y))
        # different class, but same state:
        self.assertEqual(VO4().__getstate__(), VO7().__getstate__())
        # __setstate__
        v1 = VO5('a')
        v2 = VO5('', s5=34)
        self.assertNotEqual(v1, v2)
        v1.__setstate__(v2.__getstate__())
        self.assertEqual(v1, v2)
        self.assertRaises(ValueError, v1.__setstate__, VO6().__getstate__())

    def test_eq(self):
        self.assertEqual(VO1(), VO1())
        self.assertEqual(VO2(9), VO2(9))
        self.assertNotEqual(VO2(9), VO2(8))
        self.assertNotEqual(VO1(), VO2())
        self.assertEqual(VO5('abc'), VO5('abc', s5=9))
        # class with __getstate__:
        self.assertEqual(VO6(), VO6())
        self.assertNotEqual(VO6(), VO2())
        # same state, but different class:
        self.assertNotEqual(VO4(), VO7())

    def test_hash(self):
        val = VO5(8)
        self.assertEqual(hash(val), hash((val.__class__, val.__getstate__())))
        # class with __getstate__:
        val = VO6()
        self.assertEqual(hash(val), hash((val.__class__, val.__getstate__())))
        # same state, but different class:
        self.assertNotEqual(hash(VO4()), hash(VO7()))

    def test_copy(self):
        val = VO5(8)
        self.assertTrue(copy(val) is val)


if __name__ == '__main__':
    unittest.main()
