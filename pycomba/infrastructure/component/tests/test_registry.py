#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Name:        test_registry
# Purpose:     Test driver for module registry
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2016 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

from typing import Any
import unittest
from pycomba.infrastructure.component import Component
from pycomba.infrastructure.component.registry import (
    ComponentLookupError, ComponentRegisterError,
    get_component_registry, get_utility, register_factory, register_utility)


class Meta(type):

    pass


def unknown_return_type():
    pass


class Int2Str:

    def __call__(self, i: int) -> str:
        return str(i)


def int_2_str(i: int) -> str:
    return str(i)


def Int2StrFactory() -> Int2Str:
    return int_2_str


class Util1(Component):

    def __init__(self):
        pass


class Util2(Util1):

    pass


class Util3(Util2):

    pass


class Util3Sub1(Util3):

    pass


class Util3Sub2(Util3Sub1):

    pass


class Util4(Util2):

    pass


def Util4Factory() -> Util4:
    return Util4()


class RegistryTest(unittest.TestCase):

    def setUp(self):
        self.registry = get_component_registry()

    def test_global_registry(self):
        self.assertIs(self.registry, get_component_registry())

    def test_register_factory(self):
        # no signature
        self.assertRaises(ComponentRegisterError, register_factory, Meta)
        # interface 'Any'
        self.assertRaises(ComponentRegisterError, register_factory,
                          unknown_return_type)
        self.assertRaises(ComponentRegisterError, register_factory,
                          Int2Str, Any)
        # factory not returning instance of interface
        self.assertRaises(ComponentRegisterError, register_factory,
                          Int2Str, str)
        # factory w/o interface given
        register_factory(Int2Str)
        self.assertIn(Int2Str, self.registry._factories[(Int2Str, None)])
        register_factory(Int2Str, name='int2str')
        self.assertIn(Int2Str, self.registry._factories[(Int2Str, 'int2str')])
        # registering already registered factory
        register_factory(Int2Str)
        self.assertEqual(self.registry._factories[(Int2Str, None)], [Int2Str])
        register_factory(Int2Str, name='int2str')
        self.assertEqual(self.registry._factories[(Int2Str, 'int2str')],
                         [Int2Str])
        # registering another factory with same interface
        register_factory(Int2StrFactory, Int2Str)
        self.assertEqual(self.registry._factories[(Int2Str, None)],
                         [Int2Str, Int2StrFactory])
        register_factory(Int2StrFactory, Int2Str, name='int2str')
        self.assertEqual(self.registry._factories[(Int2Str, 'int2str')],
                         [Int2Str, Int2StrFactory])

    def test_register_utility(self):
        # interface 'Any'
        self.assertRaises(ComponentRegisterError, register_utility,
                          unknown_return_type, Any)
        # function given as utility w/o interface given
        self.assertRaises(ComponentRegisterError, register_utility,
                          unknown_return_type)
        # utility doesn't implement given interface
        self.assertRaises(ComponentRegisterError, register_utility,
                          Util1(), Util2)
        # function with corresponding interface
        register_utility(int_2_str, Int2Str)
        self.assertIn(int_2_str, self.registry._utilities[(Int2Str, None)])
        register_utility(int_2_str, Int2Str, name='int_2_str')
        self.assertIn(int_2_str,
                      self.registry._utilities[(Int2Str, 'int_2_str')])
        # registering already registered utility
        register_utility(int_2_str, Int2Str)
        self.assertEqual(self.registry._utilities[(Int2Str, None)],
                         [int_2_str])
        register_utility(int_2_str, Int2Str, name='int_2_str')
        self.assertEqual(self.registry._utilities[(Int2Str, 'int_2_str')],
                         [int_2_str])
        # registering another utility with same interface
        register_utility(int.__str__, Int2Str)
        self.assertEqual(self.registry._utilities[(Int2Str, None)],
                         [int_2_str, int.__str__])
        register_utility(int.__str__, Int2Str, name='int_2_str')
        self.assertEqual(self.registry._utilities[(Int2Str, 'int_2_str')],
                         [int_2_str, int.__str__])
        # component w/o interface given
        util = Util1()
        register_utility(util)
        self.assertEqual(self.registry._utilities[(Util1, None)], [util])

    def test_get_utility(self):
        name = 'utils'
        # instance w/o interface given
        util = Util2()
        register_utility(util)
        self.assertIs(get_utility(Util2), util)
        register_utility(util, name=name)
        self.assertIs(get_utility(Util2, name=name), util)
        # another class registered with same interface
        util = Util3()
        register_utility(util, Util2, name=name)
        self.assertIs(get_utility(Util2, name=name), util)
        # more general interface
        self.assertIs(get_utility(Util1, name=name), util)
        # no utility registered
        self.assertRaises(ComponentLookupError, get_utility, Util3, name=name)
        # no utility registered, but corresponding factory
        register_factory(Util4Factory, name=name)
        self.assertIsInstance(get_utility(Util4, name=name), Util4)

    # def tearDown(self):
    #     pass


if __name__ == '__main__':
    unittest.main()
