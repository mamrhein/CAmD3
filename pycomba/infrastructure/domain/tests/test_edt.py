#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_edt
# Purpose:     Test driver for module edt
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

from enum import Enum
from operator import getitem
import unittest
from pycomba.infrastructure import Attribute
from pycomba.infrastructure.domain.edt import EDT, EDTMeta


Color = Enum('Color', 'red green blue')


class EDTTest(unittest.TestCase):

    def setUp(self):
        class ColorMap(EDT, enum=Color):
            a = Attribute()
            b = Attribute()
        self.color_map = ColorMap

    def test_meta(self):
        ColorMap = self.color_map
        self.assertRaises(TypeError, EDTMeta, 'Ext', (ColorMap,), {})
        self.assertIs(ColorMap.enum, Color)
        self.assertFalse(ColorMap._sealed)

    def test_init(self):
        ColorMap = self.color_map
        self.assertRaises(AssertionError, ColorMap, 4, 9, 'X')
        blue = ColorMap(Color.blue, 3, 'B')
        self.assertEqual(blue.name, 'blue')
        self.assertEqual(blue.code, 3)
        self.assertEqual(blue.a, 3)
        self.assertEqual(blue.b, 'B')
        self.assertRaises(ValueError, ColorMap, Color.blue, 6, 'B')

    def test_instance_dict(self):
        ColorMap = self.color_map
        red = ColorMap(Color.red, 1, 'R')
        blue = ColorMap(Color.blue, 3, 'B')
        self.assertIs(ColorMap[Color.red], red)
        self.assertIs(ColorMap[Color.blue], blue)
        self.assertRaises(KeyError, getitem, ColorMap, Color.green)
        self.assertIn(red, ColorMap)
        self.assertEqual(len(ColorMap), 2)
        self.assertEqual(set(ColorMap), {red, blue})
        green = ColorMap(Color.green, 2, 'G')
        self.assertIs(ColorMap[Color.green], green)
        self.assertIn(green, ColorMap)
        self.assertEqual(len(ColorMap), 3)
        self.assertEqual(set(ColorMap), {red, green, blue})

    def test_populate_from_list(self):
        ColorMap = self.color_map
        ColorMap.populate([(Color.green, 2, 'G')],
                          complete=False)
        self.assertEqual(len(ColorMap), 1)
        ColorMap.populate([(Color.blue, 3, 'B')])
        self.assertEqual(len(ColorMap), 2)
        blue = ColorMap[Color.blue]
        self.assertEqual(blue.name, 'blue')
        self.assertEqual(blue.code, 3)
        self.assertEqual(blue.a, 3)
        self.assertEqual(blue.b, 'B')
        self.assertRaises(TypeError, ColorMap.populate, [(Color.red, 1, 'R')])

    def test_populate_from_dict(self):
        ColorMap = self.color_map
        ColorMap.populate({Color.red: (1, 'R'),
                           Color.green: (2, 'G'),
                           Color.blue: (3, 'B')})
        blue = ColorMap[Color.blue]
        self.assertEqual(blue.name, 'blue')
        self.assertEqual(blue.code, 3)
        self.assertEqual(blue.a, 3)
        self.assertEqual(blue.b, 'B')

    def test_repr(self):
        ColorMap = self.color_map
        red = ColorMap(Color.red, 1, 'R')
        self.assertEqual(repr(red), "%s[%s(%r)]" % ('ColorMap', 'Color', 1))

if __name__ == '__main__':
    unittest.main()
