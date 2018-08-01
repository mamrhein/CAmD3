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
import camd3.gbbs.bson as bson


class CEST(tzinfo):

    def utcoffset(self, dt):
        return timedelta(hours=2)

    def tzname(self, dt):
        return str("CEST")

    def dst(self, dt):
        return timedelta(hours=1)

cest = CEST()


class DecimalTest(unittest.TestCase):

    def test_decimal(self):
        d = Decimal('-16.7390')
        code, buf = bson.decimal2bson(d)
        self.assertEqual(code, bson.BSON_BINARY)
        bval = buf[4:]
        subtype = bval[:1]
        self.assertEqual(subtype, bson.BSON_BINARY_CUSTOM)
        self.assertEqual(d, bson.bson2decimal(bval[1:]))
        self.assertRaises(AssertionError, bson.decimal2bson, 7)
        self.assertRaises(OverflowError, bson.decimal2bson, Decimal('1E-129'))
        d = Decimal(5)
        code, buf = bson.decimal2bson(d)
        bval = buf[4:]
        i = bson.bson2decimal(bval[1:])
        self.assertEqual(i, 5)
        self.assertIsInstance(i, int)


class BSONTest(unittest.TestCase):

    def test_obj(self):
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
        bson_repr = bson.dumps(obj)
        robj = bson.loads(bson_repr)
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

    def test_list(self):
        # BSON cannot encode a list as primary document
        self.assertRaises(TypeError, bson.dumps, ['a', 5, uuid1()])

    def test_exceptions(self):
        self.assertRaises(ValueError, bson.dumps, int)
        self.assertRaises(ValueError, bson.dumps, lambda x: x)
        bson_repr = bson.dumps({"id": uuid1()})
        # test illegal BSON documents
        bson_doc = bytearray(bson_repr)
        # trailing byte != \x00
        bson_doc[-1] = 57
        self.assertRaises(ValueError, bson.loads, bson_doc)
        # unknown BSON type code
        bson_doc = bytearray(bson_repr)
        bson_doc[4] = 57
        self.assertRaises(ValueError, bson.loads, bson_doc)
        # unknown BSON binary subtype code
        bson_doc = bytearray(bson_repr)
        bson_doc[12] = 57
        self.assertRaises(ValueError, bson.loads, bson_doc)


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
                return dict((('@%i' % i, e) for i, e in enumerate(obj)))
            return None

        encoders = {Fraction: fraction2bson}
        self.encoder = bson.BSONEncoder(encoders=encoders,
                                        transformers=[transform_set])

        def bson2fraction(bval):
            """Decode BSON Binary / Custom as Fraction."""
            numerator, denominator = unpack('<qq', bval)
            return Fraction(numerator, denominator)

        def recreate_set(dict_):
            if '@0' in dict_:
                return set(dict_.values())

        decoders = {bson.BSON_BINARY + bson.BSON_BINARY_CUSTOM: bson2fraction}
        self.decoder = bson.BSONDecoder(decoders=decoders,
                                        recreators=[recreate_set])

    def test_obj(self):
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
