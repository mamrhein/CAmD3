#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        test_uidattr
# Purpose:     Test driver for module 'uidattr'
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2018 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Test driver for module 'uidattr'"""


import unittest
from uuid import uuid1

from camd3.infrastructure.component import (
    Component, register_utility, UniqueIdAttribute)
from camd3.infrastructure.component.idfactories import (
    UUIDGenerator, uuid_generator)


# factory for UUIDs
def custom_uuid_generator() -> UUIDGenerator:                   # noqa: D103
    while True:
        yield uuid1()


class ExplID(Component):

    id = UniqueIdAttribute(uid_gen=custom_uuid_generator())

    def __init__(self):
        self.__class__.id.set_once(self)


class ImplID(Component):

    id = UniqueIdAttribute()

    def __init__(self):
        self.__class__.id.set_once(self)


class UniqueIdAttributeTest(unittest.TestCase):

    def setUp(self):
        register_utility(uuid_generator(), UUIDGenerator)
        self.cid = ImplID()

    def test_init(self):
        cid = ImplID()
        self.assertIsNotNone(cid.id)
        self.assertIsNotNone(cid._id)

    def test_uniqueness(self):
        ids = {self.cid.id}
        for i in range(10):
            cid = ExplID()
            self.assertNotIn(cid.id, ids)
            ids.add(cid.id)


if __name__ == '__main__':                              # pragma: no cover
    unittest.main()
