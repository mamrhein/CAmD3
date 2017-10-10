#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Name:        test_reference
# Purpose:     Test driver for module 'reference'
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2017 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

from enum import Enum
import gc
import unittest
from uuid import uuid1

from pycomba.infrastructure.component import Component
from pycomba.infrastructure.component.reference import (
    Reference, UniqueIdentifier)


class Tire:

    def __init__(self, make: str, size: str) -> None:
        self.make = make
        self.size = size


RimType = Enum('RimType', ('alu', 'steel'))


class Wheel:

    def __init__(self, type_of_rim: RimType, tire: Tire) -> None:
        self.type_of_rim = type_of_rim
        self.tire = tire


WheelPosition = Enum('WheelPosition',
                     ('front_left', 'front_right', 'rear_left', 'rear_right'))


class Car(Component):

    _all_car_specs = {}

    def __init__(self, make: str, model: str, type_of_rim: RimType,
                 tire: Tire):
        super().__init__(self)
        self.id = id = uuid1()
        self._all_car_specs[id] = {
            'make': make,
            'model': model,
            'type_of_rim': type_of_rim,
            'tire': tire}
        self.make = make
        self.model = model
        self.wheels = {pos: Wheel(type_of_rim, tire)
                       for pos in WheelPosition}


def uid2car(id: UniqueIdentifier) -> Car:
    return Car(**Car._all_car_specs[id])


class UniqueIdentifierTest1(unittest.TestCase):

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


class UniqueIdentifierTest2(unittest.TestCase):

    def setUp(self):
        self.mybmw = Car(make="BMW", model="330i", type_of_rim=RimType.alu,
                         tire=Tire("GoodYear", '18"'))

    def test_adapt(self):
        mybmw = self.mybmw
        self.assertIs(UniqueIdentifier[mybmw], mybmw.id)

    # def tearDown(self):
    #     pass


class ReferenceTest1(unittest.TestCase):

    def setUp(self):
        mybmw = Car(make="BMW", model="330i", type_of_rim=RimType.alu,
                    tire=Tire("GoodYear", '18"'))
        self.mybmw_id = mybmw.id
        self.mybmw = Reference(mybmw)
        # force garbage collection
        gc.collect()

    def test_constructor(self):
        mybmw = self.mybmw
        self.assertIs(mybmw._refobj_type, Car)
        self.assertIs(mybmw._refobj_uid, self.mybmw_id)
        self.assertIsNone(mybmw._refobj_ref())

    def test_proxy(self):
        mybmw = self.mybmw
        self.assertRaises(TypeError, getattr, mybmw, 'make')
        Car.add_adapter(uid2car)
        self.assertEqual(mybmw.make, 'BMW')
        self.assertEqual(mybmw.wheels[WheelPosition.front_right].tire.size,
                         '18"')

    # def tearDown(self):
    #     pass


if __name__ == '__main__':                              # pragma: no cover
    unittest.main()
