# -*- coding: utf-8 -*-
##----------------------------------------------------------------------------
## Name:        test_immutable
## Purpose:     Test driver for module 'immutable'.
##
## Author:      Michael Amrhein (mamrhein@users.sourceforge.net)
##
## Copyright:   (c) 2014 Michael Amrhein
## License:     This program is part of a larger application. For license
##              details please read the file LICENSE.TXT provided together
##              with the application.
##----------------------------------------------------------------------------
## $Source$
## $Revision$


"""Test driver for module 'immutable'."""


import unittest
from decimal import Decimal
from camd3.infrastructure.component.immutable import Immutable, is_immutable


class T1(Immutable):
    pass


class T2(T1):
    pass


class T3(T1):
    pass


class T4(T3, T2):
    pass


class T5:
    pass


class T6(T5):
    pass


class ImmutableTest(unittest.TestCase):

    def test_inheritance(self):
        self.assertTrue(issubclass(T4, Immutable))
        t4 = T4()
        self.assertTrue(isinstance(t4, Immutable))

    def test_copy(self):
        t4 = T4()
        self.assertTrue(t4.__copy__() is t4)
        self.assertTrue(t4.__deepcopy__() is t4)

    def test_register(self):
        Immutable.register(T5)
        self.assertTrue(issubclass(T5, Immutable))
        t5 = T5()
        self.assertTrue(isinstance(t5, Immutable))

    def test_is_immutable(self):
        t4 = T4()
        self.assertTrue(is_immutable(t4))
        t6 = T6()
        self.assertTrue(not is_immutable(t6))
        for obj in (b'', u'', 1, 1.0, Decimal('1.1'), frozenset((1, 2, 3))):
            self.assertTrue(is_immutable(obj))
        tpl = (1, ('a', 'b'), (2, ('c', 'd', 'e')), 3)
        self.assertTrue(is_immutable(tpl))
        tpl = (1, ('a', 'b'), (2, ['c', 'd', 'e']), 3)
        self.assertTrue(not is_immutable(tpl))
        tpl = (1, set(('a', 'b')), (2, ('c', 'd', 'e')), 3)
        self.assertTrue(not is_immutable(tpl))
        self.assertTrue(not is_immutable(object()))


if __name__ == '__main__':
    unittest.main()
