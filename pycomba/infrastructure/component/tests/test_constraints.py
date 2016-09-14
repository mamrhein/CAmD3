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
import unittest
from pycomba.infrastructure.component.constraints import (instance, is_number,
                                                          is_rational, is_int,
                                                          non_negative,
                                                          between)


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


if __name__ == '__main__':
    unittest.main()
