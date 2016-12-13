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

import unittest
from pycomba.infrastructure.component.registry import (
    ComponentLookupError, ComponentRegisterError, ComponentRegistry,
    get_component_registry, get_utility, register_factory, register_utility)


def unknown_return_type():
    pass


class Int2Str:

    def __call__(self, i: int) -> str:
        return str(i)


def int_2_str(i: int) -> str:
    return str(i)


class RegistryTest(unittest.TestCase):

    def setUp(self):
        self.registry = get_component_registry()
        register_factory(Int2Str)
        register_factory(Int2Str, name='int2str')
        register_utility(int_2_str, Int2Str)
        register_utility(int_2_str, Int2Str, name='int_2_str')

    def test_global_registry(self):
        self.assertIs(self.registry, get_component_registry())

    def test_register_factory(self):
        self.assertRaises(ComponentRegisterError, register_factory,
                          unknown_return_type)
        self.assertIn(Int2Str, self.registry._factories[(Int2Str, None)])
        self.assertIn(Int2Str, self.registry._factories[(Int2Str, 'int2str')])

    def test_register_utility(self):
        self.assertRaises(ComponentRegisterError, register_utility,
                          unknown_return_type)
        self.assertIn(int_2_str, self.registry._utilities[(Int2Str, None)])
        self.assertIn(int_2_str,
                      self.registry._utilities[(Int2Str, 'int_2_str')])

    # def tearDown(self):
    #     pass


if __name__ == '__main__':
    unittest.main()
