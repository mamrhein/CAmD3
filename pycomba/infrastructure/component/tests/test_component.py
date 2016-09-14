#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_component
# Purpose:     Test driver for module component
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2014 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

from abc import ABC
from numbers import Number
import unittest
from pycomba.infrastructure.component import (Component, Immutable,
                                              implementer,)
from pycomba.infrastructure.component.component import _ABCSet


class TestComp1(Component):
    pass


class TestComp2(Component):
    pass


class TestComp3(Component, Immutable):
    pass


@implementer(TestComp1, TestComp2)
class TestImpl:
    pass


class ABCSetTest(unittest.TestCase):

    def testAdd(self):
        cls_list = (ABC, Immutable, TestComp3, Component)
        self.assertEqual(_ABCSet(cls_list), _ABCSet({ABC, TestComp3}))
        cls_list = (int, object, Number, float)
        self.assertEqual(_ABCSet(cls_list), _ABCSet({int, float}))


class ComponentTest(unittest.TestCase):

    def test_implementer(self):
        self.assertTrue(issubclass(TestImpl, TestComp1))
        self.assertTrue(issubclass(TestImpl, TestComp2))


# TODO: more tests

if __name__ == '__main__':
    unittest.main()
