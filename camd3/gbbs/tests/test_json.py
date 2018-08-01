#!/usr/bin/env python
# ----------------------------------------------------------------------------
# Name:        test_json
# Purpose:     Test driver for module json
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2015 Michael Amrhein
# ----------------------------------------------------------------------------
# $Source$
# $Revision$

import unittest
from datetime import date, datetime, time, timedelta, tzinfo
from decimal import Decimal
from fractions import Fraction
from uuid import UUID, uuid1
from io import StringIO
from itertools import zip_longest
import camd3.gbbs.json as json


#TODO: write more tests


class UTC(tzinfo):

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return str("UTC")

    def dst(self, dt):
        return timedelta(0)

utc = UTC()


class CEST(tzinfo):

    def utcoffset(self, dt):
        return timedelta(hours=2)

    def tzname(self, dt):
        return str("CEST")

    def dst(self, dt):
        return timedelta(hours=1)

cest = CEST()


class JSONTest(unittest.TestCase):

    def test_datetime(self):
        # naive datetime
        dt = datetime.now().replace(microsecond=0)  # microseconds discarded
        fdt = format(dt, json.NAIVE_DATETIME_FORMAT)
        self.assertEqual(fdt, json.datetime2json(dt))
        rdt = json.json2datetime(json.datetime2json(dt))
        self.assertTrue(isinstance(rdt, datetime))
        self.assertEqual(dt, rdt)
        # date
        d = dt.date()
        fd = format(d, json.ISO_DATE_FORMAT)
        self.assertEqual(fd, json.date2json(d))
        rd = json.json2date(json.date2json(d))
        self.assertTrue(isinstance(rd, date))
        self.assertEqual(d, rd)
        # naive time
        t = dt.time()
        ft = format(t, json.NAIVE_TIME_FORMAT)
        self.assertEqual(ft, json.time2json(t))
        rt = json.json2time(json.time2json(t))
        self.assertTrue(isinstance(rt, time))
        self.assertEqual(t, rt)
        # non-naive datetime
        dt = datetime.now(utc).replace(microsecond=0)  # see above
        fdt = format(dt, json.TZ_DATETIME_FORMAT)
        self.assertEqual(fdt, json.datetime2json(dt))
        rdt = json.json2datetime(json.datetime2json(dt))
        self.assertTrue(isinstance(rdt, datetime))
        self.assertEqual(dt, rdt)
        dt = dt.astimezone(cest)
        fdt = format(dt, json.TZ_DATETIME_FORMAT)
        self.assertEqual(fdt, json.datetime2json(dt))
        rdt = json.json2datetime(json.datetime2json(dt))
        self.assertTrue(isinstance(rdt, datetime))
        self.assertEqual(dt, rdt)
        # non-naive time
        t = dt.timetz()
        ft = format(t, json.TZ_TIME_FORMAT)
        self.assertEqual(ft, json.time2json(t))
        rt = json.json2time(json.time2json(t))
        self.assertTrue(isinstance(rt, time))
        self.assertEqual(t, rt)
        # test fall-through
        self.assertIsNone(json.json2datetime(fd))
        self.assertIsNone(json.json2datetime(ft))
        self.assertIsNone(json.json2date(fdt))
        self.assertIsNone(json.json2date(ft))
        self.assertIsNone(json.json2time(fdt))
        self.assertIsNone(json.json2time(fd))

    def test_decimal(self):
        dec = Decimal('3.9')
        # we have to use repr here because of work around (see json.py):
        self.assertEqual(str(dec), repr(json.decimal2json(dec)))
        dec = Decimal('-1234.567890')
        self.assertEqual(str(dec), repr(json.decimal2json(dec)))

    def test_uuid(self):
        id = uuid1()
        self.assertEqual(str(id), json.uuid2json(id))
        rid = json.json2uuid(json.uuid2json(id))
        self.assertTrue(isinstance(rid, UUID))
        self.assertEqual(id, rid)
        # test fall-through
        self.assertIsNone(json.json2uuid('a0b1e37240ae11e4ae2aac7ba147af6'))

    def test_list(self):
        id = uuid1()
        dt = datetime(2014, 1, 2, 22, 17, 47)
        d = dt.date()
        t = dt.time()
        obj = ['a', 17, id, dt, d, t, {'a': 1, 'b': 2}]
        json_repr = json.dumps(obj)
        robj = json.loads(json_repr)
        self.assertEqual(obj, robj)

    def test_dict(self):
        id = uuid1()
        dt = datetime(2014, 1, 2, 22, 17, 47)
        d = dt.date()
        t = dt.time()
        obj = {'id': id,
               'dt': dt,
               'bigint': 2 ** 73,
               'dec': Decimal('-12.34567890'),
               'tuple': ('astring', 4.56, 22908 * 10 ** 14, d),
               'embedded_doc': {'i32': -5,
                                'i64': 2 ** 45 + 3,
                                't': True,
                                'f': False,
                                'bin': '\x00\x03',
                                'None': None,
                                'list': [1, 2, t]}}
        json_repr = json.dumps(obj)
        robj = json.loads(json_repr)
        self.assertEqual(len(obj), len(robj))
        self.assertEqual(obj['id'], robj['id'])
        self.assertEqual(obj['dt'], robj['dt'])
        self.assertEqual(obj['bigint'], robj['bigint'])
        self.assertTrue(type(obj['bigint']), type(robj['bigint']))
        self.assertEqual(obj['dec'], robj['dec'])
        self.assertEqual(type(obj['dec']), type(robj['dec']))
        for o, r in zip_longest(obj['tuple'], robj['tuple']):
            if isinstance(o, float):    # float is reconstructed as Decimal
                o = Decimal(str(o))
            self.assertEqual(o, r)
        emb, remb = obj['embedded_doc'], robj['embedded_doc']
        for key in emb:
            self.assertEqual(emb[key], remb[key])


class EnhancedEncoderTest(unittest.TestCase):

    def setUp(self):

        def transform_set(obj):
            if isinstance(obj, set):
                return '<%s>' % (', '.join(str(e) for e in obj))
            return None

        encoders = {Fraction: lambda f: str(f)}
        self.encoder = json.JSONEncoder(encoders=encoders,
                                        transformers=[transform_set])

    def test_encode(self):
        encoder = self.encoder
        doc = {'set': set((1, 2, 3)),
               'f': Fraction(3, 4)}
        buf = StringIO()
        encoder.encode(doc, buf)
        json_repr = buf.getvalue()
        self.assertTrue(json_repr in ('{"set": "<1, 2, 3>", "f": "3/4"}',
                                      '{"f": "3/4", "set": "<1, 2, 3>"}'))
        # no encoder and no transformer
        self.assertRaises(ValueError, encoder.encode, object(), buf)
        self.assertRaises(ValueError, encoder.encode, int, buf)


class FromDict(object):

    def __init__(self, dict_):
        self.__dict__.update(dict_)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class EnhancedDecoderTest(unittest.TestCase):

    def setUp(self):

        def decode_fraction(s):
            parts = s.split('/')
            if len(parts) == 2:
                try:
                    numerator = int(parts[0])
                    denominator = int(parts[1])
                except ValueError:
                    return None
                else:
                    return Fraction(numerator, denominator)

        def decode_set(s):
            if s.startswith('<') and s.endswith('>'):
                r = '{%s}' % s[1:-1]
                try:
                    res = eval(r, {'set': set})
                except:
                    pass
                else:
                    if isinstance(res, set):
                        return res
                return None

        self.decoder = json.JSONDecoder(str_decoders=[decode_fraction,
                                                      decode_set],
                                        recreators=[FromDict])

    def test_decode(self):
        decoder = self.decoder
        json_repr = '''{"set": "<1, 2, 3>",
                       "f": "3/4",
                       "d": {"e1": 1, "ed": {}}}'''
        buf = StringIO(json_repr)
        obj = decoder.decode(buf)
        self.assertTrue(isinstance(obj, FromDict))
        self.assertTrue(isinstance(obj.d, FromDict))
        self.assertEqual(obj, FromDict({'set': set((1, 2, 3)),
                                        'f': Fraction(3, 4),
                                        'd': FromDict({'e1': 1,
                                                       'ed': FromDict({})})}))


if __name__ == '__main__':
    unittest.main()
