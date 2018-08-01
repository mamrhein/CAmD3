# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        state
# Purpose:     Retrieve and recreate state of objects
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

"""Retrieve and recreate state of objects"""

from abc import abstractmethod
from typing import Any
from .. import Component, implementer
from ...gbbs.tools import all_slot_attrs


class State(Component):

    """An interface to retrieve and recreate the state of objects."""

    @abstractmethod
    def get_state(self) -> object:
        """Get the state of the object."""

    @abstractmethod
    def set_state(self, state: object) -> object:
        """Set the state of the object."""


@implementer(State)
class StateAdapter:

    """Adapter to get the state (i.e. an instance of `class:State`) of an
    object.

    Args:
        context(Any): object to be adapted

    Returns:
        State: wrapper to get the state of `context`
    """

    def __init__(self, context: object) -> None:
        if isinstance(context, type):
            raise TypeError("Can't adapt a class (i.e. instance of type).")
        self._context = context

    def get_state(self) -> Any:
        """Get the state of the context object."""
        context = self._context
        try:
            # If context defines a __getstate__ method, return the result (if
            # it's not None).
            state = context.__getstate__()
            if state is not None:
                return state
        except AttributeError:
            pass
        # get a dict of all attributes defined via __slots__ ...
        state = dict(all_slot_attrs(context))
        # ... and update it by __dict__
        try:
            state.update(context.__dict__)
        except AttributeError:
            pass
        if state:
            return state
        raise TypeError("Unable to retrieve state of `context`.")

    def set_state(self, state: Any) -> None:
        """Set the state of the context object."""
        context = self._context
        # If context defines a __setstate__ method, just call it.
        try:
            set_state = context.__setstate__
        except AttributeError:
            pass
        else:
            set_state(state)
            return
        # Otherwise, try to recreate object from dict
        try:
            it = state.items()
        except (AttributeError, TypeError):
            pass
        else:
            for attr, value in it:
                setattr(context, attr, value)
            return
        raise TypeError(repr(context) + " has no '__setstate__' method "
                        "and given `state` is not a dict.")


# register the adapter
State.add_adapter(StateAdapter)
