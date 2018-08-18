# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        statebroker
# Purpose:     Extensions used to notify state changes
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2018 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Extensions used to notify state changes"""


# standard library imports
from abc import abstractmethod

# third-party imports


# local imports
from .component import Component, implementer
from .attribute import MultiValueAttribute
from .extension import TransientExtension


class StateChangedListener(Component):

    """Abstract base class for listeners on state changes of components.
    """

    @abstractmethod
    def register_state_changed(self, obj: Component) -> None:
        """Called when an associated instance changes its state."""


class StateChangedNotifyer(Component):

    """Abstract base class of components notifying state changes of
    components.
    """

    @abstractmethod
    def add_listener(self, listener: StateChangedListener) -> None:
        """Add `listener` to the set of registered listeners."""

    @abstractmethod
    def remove_listener(self, listener: StateChangedListener) -> None:
        """Remove `listener` from the set of registered listeners."""

    @abstractmethod
    def notify_state_changed(self, obj: Component):
        """Notify all registered listeners about a state change.

        Calls `register_state_changed` of each listener.
        """


@implementer(StateChangedNotifyer)
class StateChangedNotifyerExtension(TransientExtension):

    """Base class for notifyers of state changes of components,
    attached to the component as transient extension.
    """

    __slots__ = ('_listeners_',)

    _listeners = MultiValueAttribute(default=set())

    def __new__(cls, obj: Component) -> 'StateChangedNotifyer':
        try:                        # an instance already attached to `obj`?
            return cls.get_from(obj)
        except ValueError:
            notifyer = super().__new__(cls)
            notifyer.attach_to(obj)
            return notifyer

    def __init__(self, obj: Component) -> None:
        pass

    def add_listener(self, listener: StateChangedListener) -> None:
        self._listeners.add(listener)

    def remove_listener(self, listener: StateChangedListener) -> None:
        self._listeners.remove(listener)

    def notify_state_changed(self, obj: Component):
        for listener in self._listeners:
            listener.register_state_changed(obj)
