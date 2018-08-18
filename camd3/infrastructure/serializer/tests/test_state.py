#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_state
# Purpose:     Test driver for module state
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Test driver for module state"""


import unittest
from datetime import datetime
from uuid import uuid1
from camd3.gbbs.tools import all_slot_attrs
from camd3.infrastructure.serializer.state import State


#TODO: write more tests


class Name:

    def __init__(self, givenNames, lastName):
        self.givenNames = givenNames
        self.lastName = lastName

    @property
    def fullName(self):
        return ' '.join(self.givenNames + [self.lastName])

    def __eq__(self, other):                                    # noqa: D103
        return (self.givenNames == other.givenNames and
                self.lastName == other.lastName)


class Address:

    __slots__ = ['street', 'zipCode', 'city']

    def __init__(self, street, zipCode, city):
        self.street = street
        self.zipCode = zipCode
        self.city = city

    def __eq__(self, other):                                    # noqa: D103
        return (self.street == other.street and
                self.zipCode == other.zipCode and
                self.city == other.city)


class Person:

    def __init__(self, id, name, address):
        self.id = id
        self.name = name
        self.address = address

    def __eq__(self, other):                                    # noqa: D103
        return self.__getstate__() == other.__getstate__()

    def __getstate__(self):                                     # noqa: D103
        return (self.id, self.name.fullName, (self.address.street,
                                              self.address.zipCode,
                                              self.address.city))


class Address2(Address):

    __slots__ = ['country']

    def __init__(self, street, zipCode, city, country):
        super(Address2, self).__init__(street, zipCode, city)
        self.country = country


class Person2(Person):

    def __setstate__(self, state):                              # noqa: D103
        self.id = state[0]
        fullName = state[1]
        names = fullName.split(' ')
        self.name = Name(names[0:-1], names[-1])
        self.address = Address(*state[2])


class StateAdapterTest(unittest.TestCase):

    def testGetState(self):
        # class without __slots__
        name = Name(['Hans', 'August'], 'Bronner')
        st = State[name].get_state()
        self.assertEqual(st, name.__dict__)
        self.assertTrue(st is not self.__dict__)
        # class with __slots__
        addr = Address('Klubweg 35', 29338, 'Posemuckel')
        st = State.adapt(addr).get_state()
        for attr, val in all_slot_attrs(addr):
            self.assertEqual(st[attr], val)
        # class with inherited __slots__
        addr = Address2('Klubweg 35', 29338, 'Posemuckel', 'Takatuka')
        st = State.adapt(addr).get_state()
        for attr, val in all_slot_attrs(addr):
            self.assertEqual(st[attr], val)
        # nested types
        id = uuid1()
        name = Name(['Hans', 'August'], 'Bronner')
        addr = Address('Klubweg 35', 29338, 'Posemuckel')
        hans = Person(id, name, addr)
        st = State[hans].get_state()
        self.assertEqual(st, hans.__getstate__())
        # standard type without __dict__ and __slots__
        dt = datetime(2014, 1, 2, 22, 17, 47, 238000)
        self.assertRaises(TypeError, State[dt].get_state)
        self.assertRaises(TypeError, State[25].get_state)

    def testSetState(self):
        # class without __slots__
        name = Name(['Hans', 'August'], 'Bronner')
        name2 = object.__new__(Name)
        State[name2].set_state(name.__dict__)
        self.assertEqual(name, name2)
        # class with __slots__
        addr1 = Address('Klubweg 35', 29338, 'Posemuckel')
        st = State[addr1].get_state()
        addr2 = object.__new__(Address)
        State[addr2].set_state(st)
        for attr, val in all_slot_attrs(addr1):
            self.assertEqual(getattr(addr2, attr), val)
        # class with inherited __slots__
        addr1 = Address2('Klubweg 35', 29338, 'Posemuckel', 'Takatuka')
        st = State[addr1].get_state()
        addr2 = object.__new__(Address2)
        State[addr2].set_state(st)
        for attr, val in all_slot_attrs(addr1):
            self.assertEqual(getattr(addr2, attr), val)
        # nested types
        id = uuid1()
        name = Name(['Hans', 'August'], 'Bronner')
        addr = Address('Klubweg 35', 29338, 'Posemuckel')
        hans = Person(id, name, addr)
        st = State[hans].get_state()
        hans2 = object.__new__(Person)
        self.assertRaises(TypeError, State[hans2].set_state, st)
        hans2 = object.__new__(Person2)
        State[hans2].set_state(st)
        self.assertEqual(hans2, hans)
        # standard type without __dict__ and __slots__
        dt = datetime(2014, 1, 2, 22, 17, 47, 238000)
        self.assertRaises(TypeError, State[dt].set_state, dt)
        self.assertRaises(TypeError, State[5].set_state, 5)

    def test_failed_adaptation(self):
        self.assertRaises(TypeError, State.adapt, type)
        self.assertRaises(TypeError, State.adapt, int)
        self.assertRaises(TypeError, State.adapt, Name)


if __name__ == '__main__':
    unittest.main()
