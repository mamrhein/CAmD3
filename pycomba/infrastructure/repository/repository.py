# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        repository
# Purpose:     Base classes for repositories
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2014 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Base classes for repositories"""


from abc import abstractmethod
from ..component import Attribute, Component, implementer
from ..domain import Entity


class DuplicateIdError(Exception):

    """Exception raised when different entities with the same id are
    detected."""


class Repository(Component):

    """Dict-like object that holds entities with a given interface."""

    interface = Attribute(doc="Interface that the objects in the repository "
                          "provide.")

    @abstractmethod
    def add(entity):
        """Add entity to the repository.

        This has no effect if entity is already present in the repository."""

    @abstractmethod
    def remove(entity):
        """Remove entity from the repository.

        If entity is not present in the repository, raise a KeyError."""

    @abstractmethod
    def find(spec):
        """Find all entities in the repository which satisfy spec."""

    @abstractmethod
    def get(entityId):
        """Get the entity with the given id.

        If no such entity is present in the repository, raise a KeyError."""

    @abstractmethod
    def __len__(self):
        """len(self) -> number of entities contained in repository."""


@implementer(Repository)
class InMemoryRepository:

    """Set-like object that holds entities with a given interface."""

    def __init__(self, interface):
        assert issubclass(interface, Entity)
        self._interface = interface
        self._dict = {}

    @property
    def interface(self):
        """Interface that the objects in the repository provide."""
        return self._interface

    def add(self, entity):
        """Add entity to the repository.

        This has no effect if entity is already present in the repository."""
        assert(self._interface.providedBy(entity))
        sDict = self._dict
        key = entity.id
        try:
            if sDict[key] is entity:
                return
            raise DuplicateIdError
        except KeyError:
            sDict[key] = entity

    def remove(self, entity):
        """Remove entity from the repository.

        If entity is not present in the repository, raise a KeyError."""
        sDict = self._dict
        key = entity.id
        if sDict[key] is entity:
            del sDict[key]
        else:
            raise DuplicateIdError

    def find(self, spec):
        """Find all entities in the repository which satisfy spec."""
        return (entity for entity in self._dict.values() if spec(entity))

    def get(self, entityId):
        """Get the entity with the given id.

        If no such entity is present in the repository, raise a KeyError."""
        return self._dict[entityId]

    def __len__(self):
        """len(self) -> number of entities contained in repository."""
        return len(self._dict)
