#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        test_statebroker
# Purpose:     Test driver for module 'statebroker'
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2018 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Test driver for module 'statebroker'"""


import unittest

from camd3.infrastructure.component import (
    Attribute, Component, implementer, StateChangedListener,
    StateChangedNotifyer)
from camd3.infrastructure.component.statebroker import (
    StateChangedNotifyerExtension)


class Comp1(Component):

    x = Attribute()

    def __init__(self, x):
        self.x = x

    def __setattr__(self, name, value):                         # noqa: D103
        super().__setattr__(name, value)
        try:
            notifyer = StateChangedNotifyer[self]
        except ValueError:
            pass
        else:
            notifyer.notify_state_changed(self)


@implementer(StateChangedListener)
class Listener:

    def __init__(self):
        self.changed_objs = {}

    def register_state_changed(self, obj: Comp1) -> None:
        self.changed_objs[obj] = obj.x


class StatebrokerTest(unittest.TestCase):

    def setUp(self):
        self.listener = Listener()

    def test_state_changed(self):
        obj = Comp1(5)
        self.assertEqual(len(self.listener.changed_objs), 0)
        # attach notifyer to obj
        notifyer = StateChangedNotifyerExtension(obj)
        # there can only be one notifyer per object
        self.assertIs(notifyer, StateChangedNotifyerExtension(obj))
        # add listener
        notifyer.add_listener(self.listener)
        # nothing changed so far
        self.assertEqual(len(self.listener.changed_objs), 0)
        # change state and check listener
        obj.x = 7
        self.assertIn(obj, self.listener.changed_objs)
        self.assertEqual(self.listener.changed_objs[obj], 7)
        # add another listener
        another_listener = Listener()
        notifyer.add_listener(another_listener)
        # change state and check listeners
        obj.x = 2
        self.assertIn(obj, another_listener.changed_objs)
        self.assertEqual(another_listener.changed_objs[obj], 2)
        self.assertEqual(self.listener.changed_objs[obj], 2)
        # remove listener
        notifyer.remove_listener(another_listener)
        # change state and check listeners
        obj.x = 0
        self.assertEqual(another_listener.changed_objs[obj], 2)
        self.assertEqual(self.listener.changed_objs[obj], 0)

    # def tearDown(self):
    #     pass


if __name__ == '__main__':                              # pragma: no cover
    unittest.main()
