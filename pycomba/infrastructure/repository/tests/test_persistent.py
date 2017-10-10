#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Name:        test_persistent
# Purpose:     Test driver for module persistent
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2017 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

from copy import deepcopy
from datetime import date
import operator
import os
import shelve
import tempfile
import unittest

from pycomba.infrastructure.component import Attribute, implementer
from pycomba.infrastructure.domain import Entity
from pycomba.infrastructure.repository.objstore import ObjectStore
from pycomba.infrastructure.repository.persistent import (
    Persistent, PersistentRepository, PersistenceState)
from pycomba.infrastructure.repository.repository import DuplicateIdError
from pycomba.infrastructure.specification import ValueSpecification


# register DbfilenameShelf as ObjStore
implementer(ObjectStore)(shelve.DbfilenameShelf)


class DummyEntity(Entity):

    id = Attribute(immutable=True)

    def __init__(self):
        self.id = id(self)


class Person(Entity):

    id = Attribute(immutable=True)
    first_name = Attribute()
    last_name = Attribute()
    date_of_birth = Attribute()

    def __init__(self, first_name, last_name, date_of_birth):
        self.id = str(hash((first_name, last_name, date_of_birth)))
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth


class Prospect(Person):

    interests = Attribute()

    def __init__(self, first_name, last_name, date_of_birth,
                 interests='not known yet'):
        super().__init__(first_name, last_name, date_of_birth)
        self.interests = interests


PERSONS = [
    Person('Hans', 'Berlinger', date(1954, 7, 14)),
    Person('Hans', 'Berliner', date(1980, 12, 4)),
    Prospect('Bert', 'Berlinger', date(1974, 5, 11), ('Party equipment',)),
]


class PersistentTest(unittest.TestCase):

    def test_constructor(self):
        dummy = DummyEntity()
        ext = Persistent(dummy)
        self.assertIs(Persistent[dummy], ext)
        self.assertEqual(ext.state, PersistenceState.SAVED)
        duplicate = deepcopy(dummy)
        self.assertRaises(ValueError, operator.getitem, Persistent, duplicate)

    def test_attr_access(self):
        dummy = DummyEntity()
        ext = Persistent(dummy)
        self.assertRaises(ValueError, setattr, ext, 'state', 7)


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
        self.objstore = objstore = ObjectStore[shelve.open(filename)]
        self.repo = PersistentRepository(Person, objstore)

    def test_contains(self):
        repo = self.repo
        for p in PERSONS:
            self.assertNotIn(p, repo)
        p1 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertNotIn(p1, repo)
        self.assertIsNone(repo.add(p1))
        self.assertIn(p1, repo)
        p2 = deepcopy(p1)
        self.assertNotIn(p2, repo)

    def test_add(self):
        repo = self.repo
        self.assertEqual(len(repo), 3)
        for p in PERSONS:
            self.assertRaises(DuplicateIdError, repo.add, p)
        p1 = Prospect('Hans', 'Berlinger', date(1982, 12, 13))
        self.assertNotIn(p1, repo)
        self.assertIsNone(repo.add(p1))
        self.assertIn(p1, repo)
        self.assertEqual(len(repo), 4)
        p2 = deepcopy(p1)
        self.assertRaises(DuplicateIdError, repo.add, p2)
        dummy = DummyEntity()
        self.assertRaises(AssertionError, repo.add, dummy)

    def test_remove(self):
        repo = self.repo
        p1 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertIsNone(repo.add(p1))
        self.assertEqual(len(repo), 4)
        p2 = deepcopy(p1)
        self.assertRaises(DuplicateIdError, repo.remove, p2)
        p3 = Prospect('Hans', 'Berlinger', date(1982, 12, 13))
        self.assertRaises(KeyError, repo.remove, p3)
        self.assertIsNone(repo.remove(p1))
        self.assertEqual(len(repo), 3)

    def test_get(self):
        repo = self.repo
        for p in PERSONS:
            self.assertIsNot(p, repo.get(p.id))
        p1 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertIsNone(repo.add(p1))
        self.assertIs(repo.get(p1.id), p1)
        p3 = Prospect('Hans', 'Berlinger', date(1982, 12, 13))
        self.assertRaises(KeyError, repo.get, p3.id)
        self.assertIsNone(repo.add(p3))
        self.assertIs(repo.get(p3.id), p3)

    # def test_find(self):
    #     repo = self.repo
    #     p1, p2, p3 = PERSONS
    #     p4 = Person('Hans', 'Berlinger', date(1982, 12, 3))
    #     repo.add(p4)
    #     spec = ValueSpecification(Person, 'date_of_birth', operator.ge,
    #                               date(1980, 1, 1))
    #     res = list(repo.find(spec))
    #     self.assertEqual(len(res), 2)
    #     self.assertNotIn(p1, res)
    #     self.assertIn(p2, res)
    #     self.assertNotIn(p3, res)
    #     self.assertIn(p4, res)

    def tearDown(self):
        self.objstore.close()


if __name__ == '__main__':                              # pragma: no cover
    unittest.main()
