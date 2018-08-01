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


# standard lib imports
from abc import abstractmethod
from collections import Container, Sized
from typing import Any, Iterable

# third-party imports
from specification import Specification

# local imports
from ..component import Attribute, Component, subclass
from ..domain import Entity


class DuplicateIdError(Exception):

    """Exception raised when different entities with the same id are
    detected."""


class Repository(Component, Container, Sized):

    """Container that holds entities with a given interface."""

    interface = Attribute(immutable=True,
                          constraints=subclass(Entity),
                          doc="Interface that the objects in the repository "
                          "provide.")

    @abstractmethod
    def add(self, entity: Entity) -> None:
        """Add entity to the repository.

        This has no effect if entity is already present in the repository."""

    @abstractmethod
    def remove(self, entity: Entity) -> None:
        """Remove entity from the repository.

        If entity is not present in the repository, raise a KeyError."""

    @abstractmethod
    def find(self, spec: Specification) -> Iterable[Entity]:
        """Find all entities in the repository which satisfy spec."""

    @abstractmethod
    def get(self, entityId: Any) -> Entity:
        """Get the entity with the given id.

        If no such entity is present in the repository, raise a KeyError."""

    @abstractmethod
    def __len__(self):
        """len(self) -> number of entities contained in repository."""


class InMemoryRepository(Repository):

    """Non-persistent container that holds entities with a given interface."""

    def __init__(self, interface: Entity) -> None:
        self.interface = interface
        self._dict = {}

    def add(self, entity: Entity) -> None:
        """Add entity to the repository.

        This has no effect if entity is already present in the repository."""
        assert isinstance(entity, self._interface)
        dict_ = self._dict
        key = entity.id
        try:
            if dict_[key] is entity:
                return
            raise DuplicateIdError
        except KeyError:
            dict_[key] = entity

    def remove(self, entity: Entity) -> None:
        """Remove entity from the repository.

        If entity is not present in the repository, raise a KeyError."""
        dict_ = self._dict
        key = entity.id
        if dict_[key] is entity:
            del dict_[key]
        else:
            raise DuplicateIdError

    def find(self, spec: Specification) -> Iterable[Entity]:
        """Find all entities in the repository which satisfy spec."""
        return (entity for entity in self._dict.values() if spec(entity))

    def get(self, entityId: Any) -> Entity:
        """Get the entity with the given id.

        If no such entity is present in the repository, raise a KeyError."""
        return self._dict[entityId]

    def __contains__(self, entity: Entity) -> bool:
        """`entity` in self -> True if `entity` contained in repository."""
        try:
            value = self._dict[entity.id]
        except KeyError:
            return False
        return value is entity

    def __len__(self) -> int:
        """len(self) -> number of entities contained in repository."""
        return len(self._dict)
