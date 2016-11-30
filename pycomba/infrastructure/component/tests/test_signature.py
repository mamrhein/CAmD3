#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_signature
# Purpose:     Test driver for module signature
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2016 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


import unittest
from typing import Any, Dict, Optional, Union
from pycomba.infrastructure.component.signature import (
    _get_constructor, _type_repr, _is_compatible, Signature, signature
)


class Meta(type):

    def __call__(self, a: str, i: int):
        pass


class WithInit(metaclass=Meta):

    def __new__(cls):
        pass

    def __init__(self, a: Dict, b: tuple, *args: int, c: str = '') -> None:
        pass


class WithOutInit(metaclass=Meta):

    def __new__(cls, a: Dict, b: 'WithInit', c: str = '') -> 'WithOutInit':
        pass


class WithoutInitAndNew(metaclass=Meta):

    pass


def func1(a: int, b: float, c: str, o: str = '', x: object = Optional[str]) \
        -> Signature:
    pass


def func2(a: int, b: Union[int, float], *c: 'WithInit') -> 'WithInit':
        pass


def func3():
    pass


def func4(*, x, y):
    pass


def func5(x: int, y):
    pass


def func6(x: int, y: 'kribel'):
    pass


class SignatureTest(unittest.TestCase):

    def setUp(self):
        # Called before the first testfunction is executed
        pass

    def test_constructor(self):
        arg_types = [str, int]
        var_arg_type = int
        return_type = Optional[Dict]
        sig = Signature(arg_types, var_arg_type, return_type)
        self.assertEqual(sig.arg_types, tuple(arg_types))
        self.assertIs(sig.var_arg_type, var_arg_type)
        self.assertIs(sig.return_type, return_type)

    def test_ops(self):
        s1 = Signature([Dict, float], None, object)
        self.assertEqual(s1.__getstate__(), ((Dict, float), None, object))
        s2 = Signature([Dict, float], None, object)
        self.assertEqual(s2.__getstate__(), ((Dict, float), None, object))
        s3 = Signature([Dict, float, float], int, str)
        self.assertEqual(s3.__getstate__(), ((Dict, float, float), int, str))
        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        self.assertNotEqual(s3, s2)
        self.assertEqual(hash(s3), hash(((Dict, float, float), int, str)))

    def test_get_constructor(self):
        self.assertIs(_get_constructor(WithInit), WithInit.__init__)
        self.assertIs(_get_constructor(WithOutInit), WithOutInit.__new__)
        self.assertIs(_get_constructor(WithoutInitAndNew), Meta.__call__)
        self.assertIsNone(_get_constructor(object))
        self.assertIsNone(_get_constructor(all))

    def test_signature(self):
        self.assertEqual(signature(WithInit),
                         Signature((Dict, tuple), int, WithInit))
        self.assertEqual(signature(WithOutInit),
                         Signature((Dict, WithInit), None, WithOutInit))
        self.assertEqual(signature(WithoutInitAndNew),
                         Signature((str, int), None, WithoutInitAndNew))
        self.assertEqual(signature(func1),
                         Signature((int, float, str), None, Signature))
        self.assertEqual(signature(func2),
                         Signature((int, Union[int, float]),
                                   WithInit, WithInit))
        self.assertEqual(signature(func3),
                         Signature((), None, Any))
        # keyword-only args w/o default value
        self.assertRaises(ValueError, signature, func4)
        # arg w/o type hint
        self.assertRaises(ValueError, signature, func5)
        self.assertRaises(ValueError, signature, func6)
        # no signature
        self.assertRaises(ValueError, signature, int)
        self.assertRaises(ValueError, signature, 5)

    def test_is_compatible(self):
        s0 = Signature((), None, None)
        self.assertTrue(s0.is_compatible_to(s0))
        s1 = Signature([Dict, float], None, object)
        s2 = Signature([Dict, float], None, object)
        self.assertTrue(s1.is_compatible_to(s1))
        self.assertTrue(s1.is_compatible_to(s2))
        self.assertTrue(s2.is_compatible_to(s1))
        s3 = Signature((), None, object)
        s4 = Signature((), None, str)
        self.assertTrue(s4.is_compatible_to(s3))
        self.assertFalse(s3.is_compatible_to(s4))
        self.assertFalse(s3.is_compatible_to(s0))
        self.assertFalse(s4.is_compatible_to(s0))
        self.assertFalse(s0.is_compatible_to(s3))
        self.assertFalse(s0.is_compatible_to(s4))
        s6 = Signature((), object, None)
        s7 = Signature((), str, None)
        self.assertTrue(s6.is_compatible_to(s7))
        self.assertFalse(s7.is_compatible_to(s6))
        self.assertFalse(s6.is_compatible_to(s0))
        self.assertFalse(s7.is_compatible_to(s0))
        self.assertFalse(s0.is_compatible_to(s6))
        self.assertFalse(s0.is_compatible_to(s7))
        s8 = Signature((object,), None, None)
        s9 = Signature((str,), None, None)
        self.assertTrue(s8.is_compatible_to(s9))
        self.assertFalse(s9.is_compatible_to(s8))
        self.assertFalse(s8.is_compatible_to(s0))
        self.assertFalse(s9.is_compatible_to(s0))
        self.assertFalse(s0.is_compatible_to(s8))
        self.assertFalse(s0.is_compatible_to(s9))
        s10 = Signature((str, str), None, None)
        self.assertFalse(s9.is_compatible_to(s10))
        self.assertFalse(s10.is_compatible_to(s9))

    def test_repr(self):
        self.assertEqual(repr(Signature((), None, None)),
                         '<Signature () -> None>')
        self.assertEqual(repr(Signature((), None, str)),
                         '<Signature () -> <str>>')
        self.assertEqual(repr(Signature((), int, str)),
                         '<Signature (*<int>) -> <str>>')
        self.assertEqual(repr(Signature((int, Union[int, float]), None, str)),
                         '<Signature (<int>, <Union[int, float]>) -> <str>>')
        self.assertEqual(repr(Signature((Union[int, float],), str, str)),
                         '<Signature (<Union[int, float]>, *<str>) -> <str>>')
        self.assertEqual(repr(Signature((), Optional[int], str)),
                         '<Signature (*<Union[int, NoneType]>) -> <str>>')

    def tearDown(self):
        # Called after the last testfunction was executed
        pass


if __name__ == '__main__':
    unittest.main()
