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

import gc
import unittest
from weakref import WeakKeyDictionary
from pycomba.infrastructure.component.extension import (
    StateExtension, TransientExtension)


class SExt1(StateExtension):

    def __init__(self):
        pass


class SExt2(StateExtension):

    def __init__(self):
        pass


class SExt2Sub1(SExt2):

    @classmethod
    def get_from(cls, obj: object) -> StateExtension:
        return super().get_from(obj)


class SExt2Sub2(SExt2):

    pass


class SExt2Sub3(SExt2, key='test_extension.SExt2Sub3'):

    pass


class TExt1(TransientExtension):

    def __init__(self):
        pass


class TExt2(TransientExtension):

    def __init__(self):
        pass


class TExt2Sub1(TExt2):

    pass


class TExt2Sub2(TExt2):

    pass


class TExt2Sub3(TExt2, obj_map=WeakKeyDictionary()):

    pass


class StateExtensionTest(unittest.TestCase):

    def setUp(self):
        class Obj:
            pass
        self.obj = Obj()

    def test_constructor(self):
        # key set?
        self.assertIsNot(SExt1._key, SExt2._key)
        self.assertIs(SExt2._key, SExt2Sub1._key)
        self.assertIs(SExt2._key, SExt2Sub2._key)
        self.assertIsNot(SExt2._key, SExt2Sub3._key)
        # adapter set?
        adapters = SExt1.__adapters__
        self.assertEqual(len(adapters), 1)
        self.assertIn(object, adapters)
        self.assertEqual(len(adapters[object]), 1)

    def test_access(self):
        obj = self.obj
        for cls in (SExt1, SExt2, SExt2Sub1, SExt2Sub2, SExt2Sub3):
            ext = cls()
            self.assertRaises(ValueError, cls.get_from, obj)
            self.assertRaises(ValueError, cls.remove_from, obj)
            ext.attach_to(obj)
            self.assertIs(cls.get_from(obj), ext)
            cls.remove_from(obj)
            self.assertRaises(ValueError, cls.get_from, obj)
            self.assertRaises(ValueError, cls.remove_from, obj)
            # obj without a __dict__
            self.assertRaises(TypeError, cls.get_from, 5)
            self.assertRaises(TypeError, ext.attach_to, 5)
            self.assertRaises(TypeError, cls.remove_from, 5)
            # obj without a writable __dict__
            self.assertRaises(TypeError, ext.attach_to, int)
            self.assertRaises(TypeError, cls.remove_from, int)
        # sub-classes using the same key
        s2 = SExt2()
        s2.attach_to(obj)
        self.assertIs(SExt2Sub1.get_from(obj), s2)
        self.assertIs(SExt2Sub2.get_from(obj), s2)
        s2 = SExt2Sub1()
        s2.attach_to(obj)
        self.assertIs(SExt2.get_from(obj), s2)
        self.assertIs(SExt2Sub2.get_from(obj), s2)
        s2 = SExt2Sub2()
        s2.attach_to(obj)
        self.assertIs(SExt2Sub1.get_from(obj), s2)
        self.assertIs(SExt2.get_from(obj), s2)

    def test_adapt(self):
        obj = self.obj
        self.assertRaises(ValueError, SExt1.adapt, obj)
        s1 = SExt1()
        s1.attach_to(obj)
        self.assertIs(SExt1.adapt(obj), s1)
        self.assertIs(SExt1[obj], s1)


class TransientExtensionTest(unittest.TestCase):

    def setUp(self):
        class Obj:
            pass
        self.obj = Obj()

    def test_constructor(self):
        self.assertIsNot(TExt1._obj_map, TExt2._obj_map)
        self.assertIs(TExt2._obj_map, TExt2Sub1._obj_map)
        self.assertIs(TExt2._obj_map, TExt2Sub2._obj_map)
        self.assertIsNot(TExt2._obj_map, TExt2Sub3._obj_map)

    def test_access(self):
        obj = self.obj
        for cls in (TExt1, TExt2, TExt2Sub1, TExt2Sub2, TExt2Sub3):
            ext = cls()
            self.assertRaises(ValueError, cls.get_from, obj)
            self.assertRaises(ValueError, cls.remove_from, obj)
            ext.attach_to(obj)
            self.assertIs(cls.get_from(obj), ext)
            cls.remove_from(obj)
            self.assertRaises(ValueError, cls.get_from, obj)
            self.assertRaises(ValueError, cls.remove_from, obj)
            # obj not weak referencable
            self.assertRaises(TypeError, cls.get_from, 5)
            self.assertRaises(TypeError, ext.attach_to, 5)
            self.assertRaises(TypeError, cls.remove_from, 5)
        # sub-classes using the same mapping
        t2 = TExt2()
        t2.attach_to(obj)
        self.assertIs(TExt2Sub1.get_from(obj), t2)
        self.assertIs(TExt2Sub2.get_from(obj), t2)
        t2 = TExt2Sub1()
        t2.attach_to(obj)
        self.assertIs(TExt2.get_from(obj), t2)
        self.assertIs(TExt2Sub2.get_from(obj), t2)
        t2 = TExt2Sub2()
        t2.attach_to(obj)
        self.assertIs(TExt2Sub1.get_from(obj), t2)
        self.assertIs(TExt2.get_from(obj), t2)

    def test_adapt(self):
        obj = self.obj
        self.assertRaises(ValueError, TExt1.adapt, obj)
        t1 = TExt1()
        t1.attach_to(obj)
        self.assertIs(TExt1.adapt(obj), t1)
        self.assertIs(TExt1[obj], t1)

    def test_transience(self):
        Obj = type(self.obj)
        obj = Obj()
        t = TExt1()
        prev_map = dict(TExt1._obj_map)
        t.attach_to(obj)
        self.assertEqual(len(TExt1._obj_map), len(prev_map) + 1)
        self.assertIn(obj, TExt1._obj_map)
        del obj
        gc.collect()                        # force gc
        self.assertEqual(TExt1._obj_map, prev_map)
        obj = Obj()
        t = TExt1()
        t.attach_to(obj)
        self.assertEqual(len(TExt1._obj_map), len(prev_map) + 1)
        self.assertIn(obj, TExt1._obj_map)
        obj = Obj()
        self.assertNotIn(obj, TExt1._obj_map)
        gc.collect()                        # force gc
        self.assertEqual(TExt1._obj_map, prev_map)


if __name__ == '__main__':
    unittest.main()
