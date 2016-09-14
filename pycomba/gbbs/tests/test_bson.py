#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_bson
# Purpose:     Test driver for module bson
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2016 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


import unittest
from struct import pack, unpack
from struct import error as StructError
from fractions import Fraction
from datetime import datetime, timedelta, tzinfo
from decimal import Decimal
from uuid import uuid1
from io import BytesIO
import pycomba.gbbs.bson as bson


class CEST(tzinfo):

    def utcoffset(self, dt):
        return timedelta(hours=2)

    def tzname(self, dt):
        return str("CEST")

    def dst(self, dt):
        return timedelta(hours=1)

cest = CEST()


class BSONTest(unittest.TestCase):

    def testObjectConversion(self):
        id = uuid1()
        dt = datetime(2014, 1, 2, 22, 17, 47, tzinfo=cest)
        obj = {'id': id,
               'dt': dt,
               'bigint': 2 ** 73,
               'dec': Decimal('-12.34567890'),
               'tuple': ('astring', 4.56, 22908 * 10 ** 14),
               'embedded_doc': {'i32': -5,
                                'i64': 2 ** 45 + 3,
                                't': True,
                                'f': False,
                                'bin': b'\x00\x03',
                                'None': None,
                                'list': [1, 2]}}
        bsonRepr = bson.dumps(obj)
        robj = bson.loads(bsonRepr)
        self.assertEqual(len(obj), len(robj))
        self.assertEqual(obj['id'], robj['id'])
        self.assertEqual(obj['dt'], robj['dt'])
        self.assertEqual(obj['bigint'], robj['bigint'])
        self.assertTrue(type(obj['bigint']), type(robj['bigint']))
        self.assertEqual(obj['dec'], robj['dec'])
        self.assertEqual(type(obj['dec']), type(robj['dec']))
        self.assertEqual(obj['dec'].as_tuple(), robj['dec'].as_tuple())
        # tuple is reconstructed as list:
        self.assertEqual(list(obj['tuple']), robj['tuple'])
        emb, remb = obj['embedded_doc'], robj['embedded_doc']
        for key in emb:
            self.assertEqual(emb[key], remb[key])


def bson2fraction(bval):
    """Decode BSON Binary / Custom as Fraction."""
    numerator, denominator = unpack('<qq', bval)
    return Fraction(numerator, denominator)


class EnhancedInterfaceTest(unittest.TestCase):

    def setUp(self):

        self.doc = {'set': set((1, 2, 3)),
                    'f': Fraction(3, 4)}

        def fraction2bson(val):
            """Encode Fraction as BSON Binary / Custom."""
            assert isinstance(val, Fraction)
            try:
                buf = pack('<qq', val.numerator, val.denominator)
            except StructError:
                raise OverflowError("Max int64 exceeded.")
            return (bson.BSON_BINARY,
                    pack('<i', len(buf)) + bson.BSON_BINARY_CUSTOM + buf)

        def transform_set(obj):
            if isinstance(obj, set):
                return list(obj)
            return None

        encoders = {Fraction: fraction2bson}
        self.encoder = bson.BSONEncoder(encoders=encoders,
                                        transformers=[transform_set])

        def bson2fraction(bval):
            """Decode BSON Binary / Custom as Fraction."""
            numerator, denominator = unpack('<qq', bval)
            return Fraction(numerator, denominator)

        def recreate_set(dict_):
            set_ = dict_['set']
            dict_['set'] = set(set_)

        decoders = {bson.BSON_BINARY + bson.BSON_BINARY_CUSTOM: bson2fraction}
        self.decoder = bson.BSONDecoder(decoders=decoders,
                                        recreators=[recreate_set])

    def testObjectConversion(self):
        doc = self.doc
        buf = BytesIO()
        encoder = self.encoder
        encoder.encode(doc, buf)
        buf.seek(0)
        decoder = self.decoder
        rdoc = decoder.decode(buf)
        self.assertEqual(doc, rdoc)


if __name__ == '__main__':
    unittest.main()
