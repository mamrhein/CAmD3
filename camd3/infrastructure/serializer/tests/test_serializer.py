#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_serializer
# Purpose:     Test driver for module serializer
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Test driver for module serializer"""


import unittest
from datetime import datetime, timedelta, tzinfo
from itertools import zip_longest
from uuid import uuid1
from camd3.infrastructure import (
    get_utility, register_factory, register_utility)
from camd3.infrastructure.serializer import (
    Encoder, EncoderFactory, Decoder, DecoderFactory)
from camd3.infrastructure.serializer.bson import (
    BSONEncoderFactory, BSONDecoderFactory)
from camd3.infrastructure.serializer.json import (
    JSONEncoderFactory, JSONDecoderFactory)
from camd3.infrastructure.serializer.serializer import (
    Serializer_, Deserializer_, IO_MODE_MAP)
from camd3.types.decimal import Decimal
from camd3.types.quantity.predefined import Mass


def setUpModule():                                              # noqa: D103
    # register needed components

    name = 'bson'
    # create encoder factory
    factory = BSONEncoderFactory()
    # register encoder factory as utility
    register_utility(factory, interface=EncoderFactory, name=name)
    # register encoder built by factory as utility
    register_utility(factory(), interface=Encoder, name=name)
    # create decoder factory
    factory = BSONDecoderFactory()
    # register decoder factory as utility
    register_utility(factory, interface=DecoderFactory, name=name)
    # register decoder built by factory as utility
    register_utility(factory(), interface=Decoder, name=name)

    name = 'json'
    # register encoder factory class as factory
    register_factory(JSONEncoderFactory, interface=EncoderFactory, name=name)
    # get encoder factory
    factory = get_utility(interface=EncoderFactory, name=name)
    # register encoder built by factory as utility
    register_utility(factory(), interface=Encoder, name=name)
    # register decoder factory class as factory
    register_factory(JSONDecoderFactory, interface=DecoderFactory, name=name)
    # get decoder factory
    factory = get_utility(interface=DecoderFactory, name=name)
    # register decoder built by factory as utility
    register_utility(factory(), interface=Decoder, name=name)


class CEST(tzinfo):

    def utcoffset(self, dt):
        return timedelta(hours=2)

    def tzname(self, dt):
        return str("CEST")

    def dst(self, dt):
        return timedelta(hours=1)


cest = CEST()


class Name:

    def __init__(self, given_names, last_name):
        self.given_names = given_names
        self.last_name = last_name

    @property
    def full_name(self):
        return ' '.join(self.given_names + [self.last_name])

    def __eq__(self, other):                                    # noqa: D103
        return (self.given_names == other.given_names and
                self.last_name == other.last_name)


class Address:

    __slots__ = ['street', 'zip_code', 'city']

    def __init__(self, street, zip_code, city):
        self.street = street
        self.zip_code = zip_code
        self.city = city

    def __eq__(self, other):                                    # noqa: D103
        return (self.street == other.street and
                self.zip_code == other.zip_code and
                self.city == other.city)


class Person:

    def __init__(self, id, name, address, weight):
        self.id = id
        self.name = name
        self.address = address
        self.weight = weight

    def __eq__(self, other):                                    # noqa: D103
        return self.__getstate__() == other.__getstate__()

    def __getstate__(self):                                     # noqa: D103
        return (self.id, self.name.full_name, (self.address.street,
                                               self.address.zip_code,
                                               self.address.city),
                self.weight)

    def __setstate__(self, state):                              # noqa: D103
        self.id = state[0]
        full_name = state[1]
        names = full_name.split(' ')
        self.name = Name(names[0:-1], names[-1])
        self.address = Address(*state[2])
        self.weight = state[3]


def create_buffer(mode):                                        # noqa: D103
    return IO_MODE_MAP[mode]()


class SerializerTest:

    """Mix-in for testing serializers."""

    def test_std_types(self):
        id = uuid1()
        dt = datetime(2014, 1, 2, 22, 17, 47, tzinfo=cest)
        obj = {'id': id,
               'dt': dt,
               'bigint': 2 ** 73,
               'dec': Decimal('-12.34567890'),
               'tuple': ('astring', 4.56, 22908 * 10 ** 14, dt),
               'embedded_doc': {'i32': -5,
                                'i64': 2 ** 45 + 3,
                                't': True,
                                'f': False,
                                'bin': '\x00\x03',
                                'None': None,
                                'list': [1, 2, dt]}}
        format = self.format
        serializer = Serializer_(format)
        buf = create_buffer(serializer.mode)
        serializer.dump(obj, buf)
        buf.seek(0)
        decoder = get_utility(Decoder, format)
        robj = decoder.decode(buf)
        self.assertEqual(len(obj), len(robj))
        self.assertEqual(obj['id'], robj['id'])
        self.assertEqual(obj['dt'], robj['dt'])
        self.assertEqual(obj['bigint'], robj['bigint'])
        self.assertEqual(obj['dec'], robj['dec'])
        for o, r in zip_longest(obj['tuple'], robj['tuple']):
            # when using 'json', float is reconstructed as Decimal
            if isinstance(o, float) and isinstance(r, Decimal):
                o = Decimal(str(o))
            self.assertEqual(o, r)
        emb, remb = obj['embedded_doc'], robj['embedded_doc']
        for key in emb:
            self.assertEqual(emb[key], remb[key])

    def test_nested_types(self):
        name = Name(['Hans', 'August'], 'Bronner')
        addr = Address('Klubweg 35', 29338, 'Posemuckel')
        id = uuid1()
        hans = Person(id, name, addr, Mass('78.2 kg'))
        format = self.format
        serializer = Serializer_(format)
        buf = create_buffer(serializer.mode)
        serializer.dump(hans, buf)
        buf.seek(0)
        decoder = get_utility(Decoder, format)
        py_repr = decoder.decode(buf)
        self.assertTrue('__class__' in py_repr)
        fullClsName = py_repr['__class__']
        self.assertEqual(fullClsName, __name__ + '.Person')
        self.assertTrue('__state__' in py_repr)
        state = py_repr.get('__state__')
        # tuples get reconstructed as lists, so we can't compare directly
        self.assertEqual((state[0], state[1], tuple(state[2])),
                         hans.__getstate__()[:3])
        self.assertEqual(state[3], {u'__class__': u'quantity.r',
                                    u'__clsargs__': [u'78.2 kg']})

    def test_exceptions(self):
        format = self.format
        serializer = Serializer_(format)
        self.assertRaises(ValueError, serializer.dumps, int)
        self.assertRaises(ValueError, serializer.dumps, lambda x: x)


class DeserializerTest:

    """Mix-in for testing deserializers."""

    def test_std_types(self):
        id = uuid1()
        dt = datetime(2014, 1, 2, 22, 17, 47, tzinfo=cest)
        obj = {'id': id,
               'dt': dt,
               'bigint': 2 ** 73,
               'dec': Decimal('-12.34567890'),
               'tuple': ('astring', 4.56, 22908 * 10 ** 14, dt),
               'embedded_doc': {'i32': -5,
                                'i64': 2 ** 45 + 3,
                                't': True,
                                'f': False,
                                'bin': '\x00\x03',
                                'None': None,
                                'list': [1, 2, dt]}}
        format = self.format
        serializer = Serializer_(format)
        deserializer = Deserializer_(format)
        buf = create_buffer(deserializer.mode)
        serializer.dump(obj, buf)
        buf.seek(0)
        robj = deserializer.load(buf)
        self.assertEqual(len(obj), len(robj))
        self.assertEqual(obj['id'], robj['id'])
        self.assertEqual(obj['dt'], robj['dt'])
        self.assertEqual(obj['bigint'], robj['bigint'])
        self.assertEqual(obj['dec'], robj['dec'])
        for o, r in zip_longest(obj['tuple'], robj['tuple']):
            # when using 'json', float is reconstructed as Decimal
            if isinstance(o, float) and isinstance(r, Decimal):
                o = Decimal(str(o))
            self.assertEqual(o, r)
        emb, remb = obj['embedded_doc'], robj['embedded_doc']
        for key in emb:
            self.assertEqual(emb[key], remb[key])

    def test_simple_type(self):
        name = Name(['Hans', 'August'], 'Bronner')
        format = self.format
        serializer = Serializer_(format)
        deserializer = Deserializer_(format)
        buf = create_buffer(deserializer.mode)
        serializer.dump(name, buf)
        buf.seek(0)
        name2 = deserializer.load(buf)
        self.assertEqual(name, name2)

    def test_nested_types(self):
        name = Name(['Hans', 'August'], 'Bronner')
        addr = Address('Klubweg 35', 29338, 'Posemuckel')
        id = uuid1()
        hans = Person(id, name, addr, Mass('78.2 kg'))
        format = self.format
        serializer = Serializer_(format)
        deserializer = Deserializer_(format)
        buf = create_buffer(deserializer.mode)
        serializer.dump(hans, buf)
        buf.seek(0)
        hans2 = deserializer.load(buf)
        self.assertEqual(hans, hans2)


class BSONSerializerTest(unittest.TestCase, SerializerTest):

    def setUp(self):
        self.format = 'bson'

    def test_list(self):
        format = self.format
        serializer = Serializer_(format)
        obj = ['a', 5, uuid1()]
        # BSON cannot encode a list as primary document
        self.assertRaises(TypeError, serializer.dumps, obj)


class BSONDeserializerTest(unittest.TestCase, DeserializerTest):

    def setUp(self):
        self.format = 'bson'


class JSONSerializerTest(unittest.TestCase, SerializerTest):

    def setUp(self):
        self.format = 'json'

    def test_list(self):
        format = self.format
        serializer = Serializer_(format)
        obj = ['a', 5, uuid1()]
        obj_repr = serializer.dumps(obj)
        buf = create_buffer(serializer.mode)
        buf.write(obj_repr)
        buf.seek(0)
        decoder = get_utility(Decoder, format)
        recr_obj = decoder.decode(buf)
        self.assertEqual(obj, recr_obj)


class JSONDeserializerTest(unittest.TestCase, DeserializerTest):

    def setUp(self):
        self.format = 'json'

    def test_list(self):
        format = self.format
        deserializer = Deserializer_(format)
        id = uuid1()
        obj_repr = '["a", 5, "%s"]' % id
        obj = deserializer.loads(obj_repr)
        self.assertEqual(obj, ['a', 5, id])


if __name__ == '__main__':
    unittest.main()
