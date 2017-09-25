#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Name:        test_objstore
# Purpose:     Test driver for module 'objstore'
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2017 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


from datetime import date
import os
import shelve
import tempfile
import unittest

from pycomba.infrastructure.component import implementer
from pycomba.infrastructure.repository.objstore import ObjectStore


# register DbfilenameShelf as ObjStore
implementer(ObjectStore)(shelve.DbfilenameShelf)


class Person:

    def __init__(self, first_name, last_name, date_of_birth):
        self.id = str(hash((first_name, last_name, date_of_birth)))
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth

    def __eq__(self, other):
        return (self.first_name, self.last_name, self.date_of_birth) == \
            (other.first_name, other.last_name, other.date_of_birth)


class Prospect(Person):

    def __init__(self, first_name, last_name, date_of_birth,
                 interests='not known yet'):
        super().__init__(first_name, last_name, date_of_birth)
        self.interests = interests


PERSONS = [
    Person('Hans', 'Berlinger', date(1954, 7, 14)),
    Person('Hans', 'Berliner', date(1980, 12, 4)),
    Prospect('Bert', 'Berlinger', date(1974, 5, 11), ('Party equipment',)),
]


class ObjstoreTest(unittest.TestCase):

    def setUp(self):
        tempdir = tempfile.TemporaryDirectory()
        filename = os.path.join(tempdir.name, 'objstore')
        db = shelve.open(filename)
        # fill-in some data
        for p in PERSONS:
            db[p.id] = p
        # close shelve and re-open it
        db.close()
        self.objstore = ObjectStore[shelve.open(filename)]

    def test_contains(self):
        objstore = self.objstore
        for p in PERSONS:
            # force use of ObjectStore.__contains__
            self.assertTrue(ObjectStore.__contains__(objstore, p.id))
        self.assertFalse(ObjectStore.__contains__(objstore, 'dummy'))

    def test_get_item(self):
        objstore = self.objstore
        for p in PERSONS:
            self.assertEqual(p, objstore[p.id])
            self.assertIsInstance(objstore[p.id], type(p))

    def test_set_item(self):
        objstore = self.objstore
        p1 = PERSONS[2]
        p1.interests = ('Balloons', 'Fireworks')
        objstore[p1.id] = p1
        p2 = objstore[p1.id]
        self.assertEqual(p1, p2)
        self.assertEqual(p1.interests, p2.interests)

    def tearDown(self):
        self.objstore.close()


if __name__ == '__main__':                              # pragma: no cover
    unittest.main()
