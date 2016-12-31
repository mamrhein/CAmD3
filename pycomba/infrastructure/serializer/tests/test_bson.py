#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_bson
# Purpose:     Test driver for wrapper module bson
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

import unittest
from pycomba.infrastructure.serializer.bson import (
    BSON_BINARY, BSON_BINARY_CUSTOM,
    decimal2bson, bson2decimal,
    BSONEncoder, BSONEncoderFactory,
    BSONDecoder, BSONDecoderFactory)
from pycomba.types.decimal import Decimal


class TestDecimal(unittest.TestCase):

    def test_decimal(self):
        d = Decimal('-16.7390')
        code, buf = decimal2bson(d)
        self.assertEqual(code, BSON_BINARY)
        bval = buf[4:]
        subtype = bval[:1]
        self.assertEqual(subtype, BSON_BINARY_CUSTOM)
        self.assertEqual(d, bson2decimal(bval[1:]))
        self.assertRaises(AssertionError, decimal2bson, 7)
        self.assertRaises(OverflowError, decimal2bson, Decimal('1E-129'))


class TestBSONEncoderFactory(unittest.TestCase):

    def setUp(self):
        self.factory = BSONEncoderFactory()

    def test_factory_with_defaults(self):
        factory = self.factory
        encoder = factory()
        self.assertIsInstance(encoder, BSONEncoder)
        self.assertIs(encoder._encoder_map[Decimal], decimal2bson)
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


class TestBSONDecoderFactory(unittest.TestCase):

    def setUp(self):
        self.factory = BSONDecoderFactory()

    def test_factory_with_defaults(self):
        factory = self.factory
        decoder = factory()
        self.assertIsInstance(decoder, BSONDecoder)
        self.assertIs(decoder._decoder_map[BSON_BINARY + BSON_BINARY_CUSTOM],
                      bson2decimal)
        self.assertEqual(decoder._recreators, [])

    def test_factory_with_params(self):
        factory = self.factory
        decimal_dec = lambda s: Decimal(s)
        recr1 = lambda x: x
        recr2 = lambda x: str(x)
        bson_decimal = BSON_BINARY + BSON_BINARY_CUSTOM
        decoder = factory(decoders={bson_decimal: decimal_dec},
                          recreators=(recr1, recr2))
        self.assertIs(decoder._decoder_map[bson_decimal], decimal_dec)
        self.assertEqual(decoder._recreators, (recr1, recr2))
