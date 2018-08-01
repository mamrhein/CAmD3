#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_json
# Purpose:     Test driver for wrapper module json
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

import unittest
from camd3.infrastructure.serializer.json import (
    decimal2json,
    JSONEncoder, JSONEncoderFactory,
    JSONDecoder, JSONDecoderFactory)
from camd3.types.decimal import Decimal


class TestDecimalEncoder(unittest.TestCase):

    def test_decimal2json(self):
        d = Decimal('-16.739')
        self.assertEqual(str(d), repr(decimal2json(d)))
        self.assertRaises(AssertionError, decimal2json, 7)


class TestJSONEncoderFactory(unittest.TestCase):

    def setUp(self):
        self.factory = JSONEncoderFactory()

    def test_factory_with_defaults(self):
        factory = self.factory
        encoder = factory()
        self.assertIsInstance(encoder, JSONEncoder)
        self.assertIs(encoder._encoder_map[Decimal], decimal2json)
        self.assertEqual(encoder._transformers, [])

    def test_factory_with_params(self):
        factory = self.factory
        decimal_enc = lambda d: str(d)
        trans1 = lambda x: x
        trans2 = lambda x: str(x)
        encoder = factory(encoders={Decimal: decimal_enc},
                          transformers=(trans1, trans2))
        self.assertIs(encoder._encoder_map[Decimal], decimal_enc)
        self.assertEqual(encoder._transformers, (trans1, trans2))


class TestJSONDecoderFactory(unittest.TestCase):

    def setUp(self):
        self.factory = JSONDecoderFactory()

    def test_factory_with_defaults(self):
        factory = self.factory
        decoder = factory()
        self.assertIsInstance(decoder, JSONDecoder)
        self.assertEqual(decoder._recreators, [])

    def test_factory_with_params(self):
        factory = self.factory
        decimal_dec = lambda s: Decimal(s)
        recr1 = lambda x: x
        recr2 = lambda x: str(x)
        decoder = factory(decoders={str: decimal_dec},
                          recreators=(recr1, recr2))
        self.assertIn(decimal_dec, decoder._str_decoders)
        self.assertEqual(decoder._recreators, (recr1, recr2))
        int_dec = lambda s: int(s)
        decoder = factory(decoders={str: [int_dec, decimal_dec]})
        self.assertIn(int_dec, decoder._str_decoders)
        self.assertIn(decimal_dec, decoder._str_decoders)
        self.assertRaises(ValueError, factory, {int: int})
