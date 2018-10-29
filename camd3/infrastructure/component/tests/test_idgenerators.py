#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_idgenerators
# Purpose:     Test driver for module idgenerators
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Test driver for module idgenerators"""


import unittest
from uuid import UUID

from camd3.infrastructure.component.idfactories import (
    uuid_generator, local_id_generator, local_num_id_generator)


class StringId(str):

    def incr(self):
        if self:
            head, tail = self[:-1], self[-1]
            if tail == 'z':
                return StringId(self + 'a')
            else:
                return StringId(head + chr(ord(tail) + 1))
        else:
            return StringId('a')


class Elem:

    def __init__(self, id):
        self.id = id


class IdGeneratorTest(unittest.TestCase):

    def testuuid_generator(self):
        idGen = uuid_generator()
        nIds = 10
        idMap = {next(idGen): i for i in range(nIds)}
        # assert that ids are unique:
        self.assertEqual(len(idMap), nIds)
        for id in idMap:
            self.assertTrue(isinstance(id, UUID))

    def testlocal_id_generator(self):
        context = []
        incr = lambda id: id.incr() if id else StringId().incr()
        idGen = local_id_generator(context, incr)
        nIds = 30
        idMap = {next(idGen): i for i in range(nIds)}
        # assert that ids are unique:
        self.assertEqual(len(idMap), nIds)
        for id in idMap:
            self.assertTrue(isinstance(id, StringId))
        id = next(idGen)
        self.assertEqual(incr(id), next(idGen))
        idStrs = ['za', 'zzx', 'e']
        context = [Elem(StringId(s)) for s in idStrs]
        idGen = local_id_generator(context, incr)
        self.assertEqual(StringId(max(idStrs)).incr(), next(idGen))

    def testlocal_num_id_generator(self):
        nIds = 10
        # no context, no start value
        idGen = local_num_id_generator()
        idMap = {next(idGen): i for i in range(1, nIds + 1)}
        # assert that ids are unique:
        self.assertEqual(len(idMap), nIds)
        for id in idMap:
            self.assertEqual(id, idMap[id])
        # no context, start value given
        start = 17
        idGen = local_num_id_generator(start=start)
        idMap = {next(idGen): i for i in range(start, start + nIds)}
        # assert that ids are unique:
        self.assertEqual(len(idMap), nIds)
        for id in idMap:
            self.assertEqual(id, idMap[id])
        # context given, no start value
        ids = [7, 18, 5]
        maxId = max(ids)
        context = [Elem(id) for id in ids]
        idGen = local_num_id_generator(context)
        self.assertEqual(maxId + 1, next(idGen))
        # context given, start value given, but in conflict
        self.assertRaises(ValueError, local_num_id_generator, context, maxId)
        # context given, start value given, no conflict
        idGen = local_num_id_generator(context, maxId + 1)
        self.assertEqual(maxId + 1, next(idGen))
        # still incremental?
        lastId = next(idGen)
        self.assertEqual(lastId + 1, next(idGen))


if __name__ == '__main__':
    unittest.main()
