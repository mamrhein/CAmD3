#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        test_uid
# Purpose:     Test driver for module 'uid'
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2018 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Test driver for module 'uid'"""


import unittest
from uuid import uuid1

from camd3.infrastructure.component import UniqueIdentifier


class UniqueIdentifierTest(unittest.TestCase):

    def test_adapt(self):
        obj = object()
        self.assertRaises(TypeError, UniqueIdentifier.adapt, obj)
        uid = uuid1()
        self.assertIs(UniqueIdentifier[uid], uid)
        obj = type('Obj', (), {})()
        obj.id = 5
        self.assertRaises(TypeError, UniqueIdentifier.adapt, obj)
        obj.id = uid
        self.assertIs(UniqueIdentifier[obj], uid)


if __name__ == '__main__':                              # pragma: no cover
    unittest.main()
