#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_constraints
# Purpose:     Test driver for module constraints
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2014 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

from fractions import Fraction
from numbers import Number
import unittest
from camd3.infrastructure.component.constraints import (
    instance, subclass, is_number, is_rational, is_int, lt, le, gt, ge,
    non_negative, between, length, max_length, min_length)


# TODO: more tests for constraints
class ConstraintTest(unittest.TestCase):

    def test_type_constraints(self):
        one_third = Fraction(1, 3)
        for num in (3, 2.7, one_third):
            self.assertTrue(is_number(num))
        for num in (3, one_third):
            self.assertTrue(is_rational(num))
        self.assertTrue(not is_rational(2.7))
        self.assertTrue(is_int(4))
        self.assertTrue(not is_int(one_third))
        self.assertTrue(instance(type)(int))
        self.assertTrue(instance(Fraction)(one_third))
        self.assertTrue(subclass(Number)(Fraction))

    def test_value_constraints(self):
        one_third = Fraction(1, 3)
        for num in (-3, 2.7, one_third):
            self.assertTrue(lt(3)(num))
            self.assertTrue(le(2.7)(num))
            self.assertTrue(gt(-7)(num))
            self.assertTrue(ge(-3)(num))
            self.assertTrue(between(-3, 2.7)(num))
        for num in (one_third, 1.3):
            self.assertTrue(non_negative(num))
        self.assertFalse(non_negative(-4))

    def test_length_constraints(self):
        s = 'abc'
        self.assertTrue(length(3)(s))
        self.assertFalse(length(5)(s))
        self.assertTrue(max_length(5)(s))
        self.assertFalse(max_length(2)(s))
        self.assertTrue(min_length(2)(s))
        self.assertTrue(min_length(3)(s))
        self.assertFalse(min_length(5)(s))


if __name__ == '__main__':
    unittest.main()
