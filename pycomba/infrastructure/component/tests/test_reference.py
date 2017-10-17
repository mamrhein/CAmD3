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
from operator import getitem
import unittest
from uuid import uuid1

from pycomba.infrastructure.component import Component, UniqueIdentifier
from pycomba.infrastructure.component.attribute import (
    Attribute, QualifiedMultiValueAttribute)
from pycomba.infrastructure.component.reference import (
    ref, Reference, ReferenceMeta)


class Tire(Component):

    make = Attribute(immutable=True)
    size = Attribute(immutable=True)

    def __init__(self, make: str, size: str) -> None:
        self.make = make
        self.size = size


RimType = Enum('RimType', ('alu', 'steel'))


class Wheel(Component):

    type_of_rim = Attribute(immutable=True)
    tire = Attribute(default=None)

    def __init__(self, type_of_rim: RimType, tire: Tire = None) -> None:
        self.type_of_rim = type_of_rim
        self.tire = tire


WheelPosition = Enum('WheelPosition',
                     ('front_left', 'front_right', 'rear_left', 'rear_right'))


class Car(Component):

    make = Attribute(immutable=True)
    model = Attribute(immutable=True)
    wheels = QualifiedMultiValueAttribute(WheelPosition)

    def __init__(self, make: str, model: str, type_of_rim: RimType,
                 tire: Tire):
        super().__init__(self)
        self.id = uuid1()
        self.make = make
        self.model = model
        self.wheels = {pos: Wheel(type_of_rim, tire)
                       for pos in WheelPosition}


class ReconstructableCar(Car):

    _all_car_specs = {}

    def __init__(self, make: str, model: str, type_of_rim: RimType,
                 tire: Tire):
        super().__init__(make, model, type_of_rim, tire)
        self._all_car_specs[self.id] = {
            'make': make,
            'model': model,
            'type_of_rim': type_of_rim,
            'tire': tire}


# add adapter that recreates 'ReconstructableCar' instance
def uid2car(id: UniqueIdentifier) -> ReconstructableCar:
    return ReconstructableCar(**ReconstructableCar._all_car_specs[id])
ReconstructableCar.add_adapter(uid2car)


class Garage(Component):

    car1 = ref(Car, doc="Parked car.")
    car2 = ref(ReconstructableCar, doc="Another parked car.")
    car3 = ref(Car)
    car4 = ref(Car, immutable=True)

    def __init__(self):
        pass


class ReferenceMetaTest(unittest.TestCase):

    def test_constructor(self):
        self.assertRaises(TypeError, Reference)
        self.assertIs(Garage.car1.ref_type, Car)
        self.assertFalse(Garage.car1.immutable)
        self.assertEqual(Garage.car1.__doc__, "Parked car.")

    def test_getitem(self):
        self.assertRaises(AssertionError, ReferenceMeta, 'Reference',
                          (Reference,), {}, ref_type=str)
        self.assertRaises(AssertionError, getitem, Reference, int)

    def test_repr(self):
        cls = Reference
        mod = cls.__module__
        self.assertEqual(repr(cls), '.'.join((mod, 'Reference')))
        cls = Reference[Car]
        self.assertEqual(repr(cls),
                         '.'.join((mod, 'Reference')) + f"[{repr(Car)}]")


class ReferenceTest1(unittest.TestCase):

    def setUp(self):
        self.garage = garage = Garage()
        garage.car1 = Car(make="BMW", model="330i", type_of_rim=RimType.alu,
                          tire=Tire("GoodYear", '18"'))
        garage.car2 = ReconstructableCar(make="Moota", model="Galaxy",
                                         type_of_rim=RimType.alu,
                                         tire=Tire("GoodYear", '17"'))
        # force garbage collection
        gc.collect()

    def test_get(self):
        garage = self.garage
        # car1 cannot be reconstructed, ...
        self.assertRaises(AttributeError, getattr, garage, 'car1')
        # ... but car2 can
        self.assertIsNone(garage._car2[1]())
        car2 = garage.car2
        self.assertEqual(car2.make, 'Moota')
        self.assertEqual(car2.wheels[WheelPosition.front_right].tire.size,
                         '17"')
        # internal reference to recreated 'Car' instance renewed?
        self.assertIsNotNone(garage._car2[1]())
        # access to unassigned reference
        self.assertRaises(AttributeError, getattr, garage, 'car3')

    def test_set(self):
        garage = self.garage
        self.assertIsNone(setattr(garage, 'car2',
                          Car('BMW', '120d', 'PT', '16"')))
        self.assertIsNone(setattr(garage, 'car4',
                          Car('BMW', '116i', 'PT', '16"')))
        self.assertRaises(AttributeError, setattr, garage, 'car4',
                          Car('BMW', '116i', 'PT', '16"'))

    def test_delete(self):
        garage = self.garage
        del garage.car2
        self.assertRaises(AttributeError, getattr, garage, 'car2')
        self.assertIsNone(delattr(garage, 'car2'))
        self.assertRaises(AttributeError, delattr, garage, 'car4')

    # def tearDown(self):
    #     pass


if __name__ == '__main__':                              # pragma: no cover
    unittest.main()
