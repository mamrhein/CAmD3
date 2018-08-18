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


"""Test driver for module domain"""


from copy import copy
from enum import Enum
import unittest
from typing import Optional

from camd3.infrastructure import register_utility
from camd3.infrastructure import Attribute
from camd3.infrastructure.component import (
    implementer, StateChangedListener, StateChangedNotifyer, UniqueIdentifier)
from camd3.infrastructure.component.attribute import (
    MultiValueAttribute, QualifiedMultiValueAttribute)
from camd3.infrastructure.component.reference import UniqueIdAttribute
from camd3.infrastructure.component.statebroker import StateChangedNotifyerExtension
from camd3.infrastructure.domain import (
    Entity, ValueObject, UUIDGenerator, uuid_generator)


# --- Entity ---

class TestEntityMissingId(Entity):

    def __init__(self):
        pass


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
        self.assertRaises(TypeError, TestEntityMissingId)
        for id in (1, 18, 'a', 'aa'):
            entity = TestEntity1(id)
            self.assertEqual(entity.id, id)

    def test_equality(self):
        classes = (TestEntity1, TestEntity2)
        ids = (1, 18, 'a', object())
        for cls1 in classes:
            for id1 in ids:
                e1 = cls1(id1)
                for cls2 in classes:
                    for id2 in ids:
                        e2 = cls2(id2)
                        self.assertNotEqual(e1, e2)
                        self.assertNotEqual(hash(e1), hash(e2))
        e1 = TestEntity1(5)
        self.assertEqual(e1, e1)


# --- Aggregate root ---

class TestAggregate(Entity):

    id = UniqueIdAttribute()

    def __init__(self, *args, **kwds):
        super().__init__(self, *args, **kwds)


class AggregateRootTest(unittest.TestCase):

    def setUp(self):
        register_utility(uuid_generator(), UUIDGenerator)

    def test_constructor(self):
        nIds = 10
        ids = set()
        for id in range(nIds):
            entity = TestAggregate()
            self.assertIs(UniqueIdentifier[entity], entity.id)
            ids.add(entity.id)
        self.assertEqual(len(ids), nIds)


# --- Embedding ---

class Tire(Entity):

    id = UniqueIdAttribute()
    make = Attribute(immutable=True)
    size = Attribute(immutable=True)

    def __init__(self, make: str, size: str) -> None:
        self.make = make
        self.size = size


RimType = Enum('RimType', ('alu', 'steel'))


class Wheel(Entity):

    id = UniqueIdAttribute()
    type_of_rim = Attribute(immutable=True)
    tire = Attribute(default=None)

    def __init__(self, type_of_rim: RimType, tire: Optional[Tire] = None) \
            -> None:
        self.type_of_rim = type_of_rim
        self.tire = tire


WheelPosition = Enum('WheelPosition',
                     ('front_left', 'front_right', 'rear_left', 'rear_right'))


class Car(Entity):

    id = UniqueIdAttribute()
    make = Attribute(immutable=True)
    model = Attribute(immutable=True)
    wheels = QualifiedMultiValueAttribute(WheelPosition, default={})
    extras = MultiValueAttribute(default=set())
    registered = Attribute(default=False)

    def __init__(self, make: str, model: str):
        super().__init__(self)
        self.make = make
        self.model = model

    def change_tire(self, wheel_pos: WheelPosition, tire: Tire) -> None:
        try:
            wheel = self.wheels[wheel_pos]
        except KeyError:
            raise ValueError(f"No {wheel_pos} wheel") from None
        wheel.tire = tire
        # setting attribute of nested entity doesn't trigger change
        # notification, so it has to be done explicitely
        self.state_changed()


class AggregateTest(unittest.TestCase):

    def setUp(self):
        self.car = Car('Gaudi', 'X7')

    def testNestedAccess(self):
        car = self.car
        # no wheels yet
        self.assertEqual(len(car.wheels), 0)
        # let's get some
        front_tire = Tire('FireStone', '18"')
        rear_tire = Tire('BridgeStone', '20"')
        car.wheels = {
            WheelPosition.front_left: Wheel(RimType.alu, front_tire),
            WheelPosition.front_right: Wheel(RimType.alu, front_tire),
            WheelPosition.rear_left: Wheel(RimType.alu, rear_tire),
            WheelPosition.rear_right: Wheel(RimType.alu, rear_tire)
        }
        # nested access
        self.assertEqual(car.wheels[WheelPosition.front_right].tire.size,
                         '18"')
        self.assertEqual(car.wheels[WheelPosition.rear_right].tire.make,
                         'BridgeStone')


@implementer(StateChangedListener)
class Listener:

    def __init__(self):
        self.count = 0

    def register_state_changed(self, obj: Entity) -> None:
        print('listener called', obj.registered, obj.extras, obj.wheels)
        self.count += 1


class StateChangedTest(unittest.TestCase):

    def setUp(self):
        self.listener = Listener()

    def test_state_changed(self):
        car = Car('Gaudi', 'Zero')
        # create notifyer and add listener
        StateChangedNotifyerExtension(car).add_listener(self.listener)
        # state changes via attributes trigger notification?
        car.registered = True
        self.assertEqual(self.listener.count, 1)
        car.extras.add('frontspoiler')
        self.assertEqual(self.listener.count, 2)
        car.wheels[WheelPosition.front_left] = Wheel(RimType.steel)
        self.assertEqual(self.listener.count, 3)
        # changing attribute of nested entity doesn't trigger change
        # notification
        car.wheels[WheelPosition.front_left].tire = Tire('Goodyear', '18"')
        self.assertEqual(self.listener.count, 3)
        # ... unless explicitely done (here via method)
        car.change_tire(WheelPosition.front_left, Tire('Goodyear', '20"'))
        self.assertEqual(self.listener.count, 4)


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

    def __getstate__(self):                                 # noqa: D105
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
