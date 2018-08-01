# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        persistent
# Purpose:     Helper classes for persistenting components
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2017 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Helper classes for persistenting components"""


# standard library imports
from enum import Enum
from typing import Any, Iterable
from weakref import WeakValueDictionary

# third-party imports
from specification import Specification

# local imports
from .objstore import ObjectStore
from .repository import DuplicateIdError, Repository
from ..component import Attribute, instance
from ..component.extension import TransientExtension
from ..domain import Entity


class PersistenceState(Enum):

    SAVED = 0
    CHANGED = 1


class Persistent(TransientExtension):

    __slots__ = ('_state',)

    state = Attribute(constraints=instance(PersistenceState),
                      doc="Persistence state of the extended object.")

    def __init__(self, obj: object,
                 initial_state: PersistenceState = PersistenceState.SAVED) \
            -> None:
        self.attach_to(obj)
        self.state = initial_state


class PersistentRepository(Repository):

    """Abstract base class for persistent containers that holds entities with
    a given interface."""

    def __init__(self, interface: Entity,
                 obj_store, search_engine = None) -> None:
        self.interface = interface
        self._cache = WeakValueDictionary()
        self._obj_store = ObjectStore[obj_store]
        if search_engine is None:
            self._search_engine = obj_store
        else:
            self._search_engine = search_engine

    def add(self, entity: Entity) -> None:
        """Add entity to the repository.

        This has no effect if entity is already present in the repository."""
        try:
            Persistent[entity]          # `entity` already persisted?
        except ValueError:
            pass                        # fall through
        else:
            return
        assert(isinstance(entity, self.interface))
        cache = self._cache
        obj_store = self._obj_store
        key = entity.id
        if key in cache or key in obj_store:
            raise DuplicateIdError
        obj_store[key] = cache[key] = entity
        Persistent(entity, PersistenceState.SAVED)

    def remove(self, entity: Entity) -> None:
        """Remove entity from the repository.

        If entity is not present in the repository, raise a KeyError."""
        cache = self._cache
        obj_store = self._obj_store
        key = entity.id
        if cache[key] is entity:
            del obj_store[key]
            del cache[key]
            Persistent.remove_from(entity)
        else:
            raise DuplicateIdError

    def find(self, spec: Specification) -> Iterable[Entity]:
        """Find all entities in the repository which satisfy spec."""
        # return (entity for entity in self._obj_store.values() if
        # spec(entity))

    def get(self, entity_id: Any) -> Entity:
        """Get the entity with the given id.

        If no such entity is present in the repository, raise a KeyError."""
        cache = self._cache
        try:
            return cache[entity_id]
        except KeyError:
            pass
        entity = self._obj_store[entity_id]
        cache[entity_id] = entity
        Persistent(entity, PersistenceState.SAVED)
        return entity

    def __contains__(self, entity: Entity) -> bool:
        """`entity` in self -> True if `entity` contained in repository."""
        try:
            value = self._cache[entity.id]
        except KeyError:
            return False
        return value is entity

    def __len__(self) -> int:
        """len(self) -> number of entities contained in repository."""
        return len(self._obj_store)
