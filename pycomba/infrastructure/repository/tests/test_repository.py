#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Name:        test_repository
# Purpose:     Test driver for module repository
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2017 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

from datetime import date
import operator
import unittest

from pycomba.infrastructure.component import Attribute
from pycomba.infrastructure.domain import Entity
from pycomba.infrastructure.repository.repository import (
    DuplicateIdError, InMemoryRepository)
from pycomba.infrastructure.specification import ValueSpecification


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


class InMemoryRepositoryTest(unittest.TestCase):

    # def setUp(self):
    #    pass

    def test_add(self):
        repo = InMemoryRepository(Person)
        p1 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertIsNone(repo.add(p1))
        self.assertIsNone(repo.add(p1))
        self.assertEqual(len(repo), 1)
        p2 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertRaises(DuplicateIdError, repo.add, p2)
        p3 = Prospect('Hans', 'Berlinger', date(1982, 12, 13))
        self.assertIsNone(repo.add(p3))
        self.assertEqual(len(repo), 2)
        dummy = DummyEntity()
        self.assertRaises(AssertionError, repo.add, dummy)

    def test_remove(self):
        repo = InMemoryRepository(Person)
        p1 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertIsNone(repo.add(p1))
        self.assertEqual(len(repo), 1)
        p2 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertRaises(DuplicateIdError, repo.remove, p2)
        p3 = Prospect('Hans', 'Berlinger', date(1982, 12, 13))
        self.assertRaises(KeyError, repo.remove, p3)
        self.assertIsNone(repo.remove(p1))
        self.assertEqual(len(repo), 0)

    def test_get(self):
        repo = InMemoryRepository(Person)
        p1 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertIsNone(repo.add(p1))
        self.assertIs(repo.get(p1.id), p1)
        p3 = Prospect('Hans', 'Berlinger', date(1982, 12, 13))
        self.assertRaises(KeyError, repo.get, p3.id)
        self.assertIsNone(repo.add(p3))
        self.assertIs(repo.get(p3.id), p3)

    def test_contains(self):
        repo = InMemoryRepository(Person)
        p1 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertNotIn(p1, repo)
        self.assertIsNone(repo.add(p1))
        self.assertIn(p1, repo)
        p2 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertNotIn(p2, repo)

    def test_find(self):
        repo = InMemoryRepository(Person)
        p1 = Person('Hans', 'Berlinger', date(1982, 12, 3))
        self.assertIsNone(repo.add(p1))
        p2 = Person('Bert', 'Berlinger', date(1962, 2, 14))
        self.assertIsNone(repo.add(p2))
        p3 = Prospect('Hans', 'Berliner', date(1982, 12, 3))
        self.assertIsNone(repo.add(p3))
        spec = ValueSpecification(Person, 'date_of_birth', operator.ge,
                                  date(1980, 1, 1))
        res = list(repo.find(spec))
        self.assertEqual(len(res), 2)
        self.assertIn(p1, res)
        self.assertIn(p3, res)

    # def tearDown(self):
    #    pass


if __name__ == '__main__':                              # pragma: no cover
    unittest.main()
