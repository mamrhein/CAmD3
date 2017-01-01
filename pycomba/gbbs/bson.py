# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        bson
# Purpose:     Simple BSON encoder / decoder
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2016 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Simple BSON encoder / decoder.

This module provides classes and functions which can be used to serialize
native Python objects to or recreate them from BSON documents (see
http://bsonspec.org/spec.html).

It only supports those BSON elements that have a counterpart in basic Python
types.

These are:

BSON Float              <=> float
BSON String             <=> str (unicode in Python 2.x)
BSON Document           <=> dict
BSON Array              <=> list / tuple
BSON Binary / Generic   <=> bytes
BSON Binary / UUID      <=> UUID
BSON Binary / Custom    <=> bytes (may be used with custom encoders/decoders)
BSON Boolean            <=> bool
BSON UTC Datetime       <=> datetime (UTC)
BSON Null               <=> None
BSON Int32 or Int64     <=> int (long in Python 2.x; depending on value)

Not supported are:

BSON Binary / Function
BSON Binary / Binary (Old)
BSON Binary / UUID (Old)
BSON Binary / MD5
BSON ObjectId
BSON Regex
BSON Javascript
BSON Javascript w/ scope
BSON Timestamp
BSON Max key
BSON Min key
"""


from datetime import datetime, timedelta, tzinfo
from decimal import Decimal
from functools import partial
from io import BytesIO
from struct import pack, unpack
from struct import error as StructError
from typing import (Any, Callable, Dict, Generator, Iterable, List, Optional,
                    Tuple, Union)
from uuid import UUID
from ..types.datetime import datetime2timestamp, timestamp2datetime
from ..types.generic import ByteStream


# some types
EncodeFunction = Callable[[object], Tuple[bytes, bytes]]
EncodeFunctionMap = Dict[type, EncodeFunction]
TransformFunction = Callable[[object], object]
DecodeFunction = Callable[[bytes], object]
DecodeFunctionMap = Dict[Any, DecodeFunction]
RecreateFunction = Callable[[Dict[str, object]], object]


# Some constants
ZERO = FALSE = b'\x00'
ONE = TRUE = b'\x01'

# BSON Version 1.0 element codes
BSON_FLOAT = b'\x01'
BSON_STRING = b'\x02'
BSON_DOCUMENT = b'\x03'
BSON_ARRAY = b'\x04'
BSON_BINARY = b'\x05'
BSON_OBJECT_ID = b'\x07'                    # not supported
BSON_BOOLEAN = b'\x08'
BSON_DATETIME = b'\x09'
BSON_NULL = b'\x0A'
BSON_REGEX = b'\x0B'                        # not supported
BSON_JAVASCRIPT = b'\x0D'                   # not supported
BSON_JAVASCRIPT_WS = b'\x0F'                # not supported
BSON_INT32 = b'\x10'
BSON_TIMESTAMP = b'\x11'                    # not supported
BSON_INT64 = b'\x12'
BSON_MAX_KEY = b'\x7F'                      # not supported
BSON_MIN_KEY = b'\xFF'                      # not supported

# BSON Version 1.0 binary subtype codes
BSON_BINARY_GENERIC = b'\x00'
BSON_BINARY_FUNCTION = b'\x01'              # not supported
BSON_BINARY_OLD = b'\x02'                   # not supported
BSON_BINARY_UUID_OLD = b'\x03'              # not supported
BSON_BINARY_UUID = b'\x04'
BSON_BINARY_MD5 = b'\x05'                   # not supported
BSON_BINARY_CUSTOM = b'\x80'

# TODO: support BSON 1.1

pack_i32 = lambda i: pack('<i', i)
unpack_i32 = lambda buf: unpack('<i', buf)[0]
sign = lambda num: 0 if num >= 0 else 1


class UTC(tzinfo):

    def utcoffset(self, dt: datetime) -> Optional[timedelta]:
        return timedelta(0)

    # def tzname(self, dt: datetime) -> str:
    #     return str("UTC")
    #
    # def dst(self, dt: datetime) -> Optional[timedelta]:
    #     return timedelta(0)


def bool2bson(val: bool) -> Tuple[bytes, bytes]:
    """Encode bool as BSON Boolean."""
    assert isinstance(val, bool)
    return BSON_BOOLEAN, ONE if val else ZERO


def bytes2bson(val: bytes) -> Tuple[bytes, bytes]:
    """Encode bytes as BSON Binary / Generic."""
    assert isinstance(val, (bytes, bytearray))
    return BSON_BINARY, pack_i32(len(val)) + BSON_BINARY_GENERIC + val


def datetime2bson(val: datetime) -> Tuple[bytes, bytes]:
    """Encode datetime as BSON UTC datetime."""
    # BSON datetime is milliseconds since the epoch
    assert isinstance(val, datetime)
    ms = int(datetime2timestamp(val) * 1000)
    return BSON_DATETIME, pack('<q', ms)


def decimal2bson(val: Decimal) -> Tuple[bytes, bytes]:
    """Encode Decimal as BSON Binary / Custom."""
    assert isinstance(val, Decimal)
    sign, digits, exp = val.as_tuple()
    mant = int(abs(val) * Decimal(10) ** -exp)
    # split mantissa into 8-bit chunks
    chunks = []
    while mant:
        chunks.append(mant & 255)
        mant = mant >> 8
    try:
        buf = pack('<Bb', sign, exp)
    except StructError:
        raise OverflowError("Max exponent exceeded.")
    buf += pack('<' + 'B' * len(chunks), *reversed(chunks))
    return BSON_BINARY, pack_i32(len(buf)) + BSON_BINARY_CUSTOM + buf


def float2bson(val: float) -> Tuple[bytes, bytes]:
    """Encode float as BSON double."""
    assert isinstance(val, float)
    return BSON_FLOAT, pack('<d', val)


def int2bson(val: int) -> Tuple[bytes, bytes]:
    """Encode integer as BSON int32 or int64 or Binary / Custom."""
    assert isinstance(val, int)
    try:
        return BSON_INT32, pack_i32(val)
    except StructError:
        try:
            return BSON_INT64, pack('<q', val)
        except StructError:
            # BSON INT64 exceeded, encode as Binary / Custom
            return decimal2bson(Decimal(val))


def none2bson(val: None) -> Tuple[bytes, bytes]:
    """Encode None as BSON NULL."""
    assert val is None
    return BSON_NULL, b''


def string2bson(val: str) -> Tuple[bytes, bytes]:
    """Encode string as BSON UTF-8 string."""
    assert isinstance(val, str)
    buf = val.encode('utf8')
    return BSON_STRING, pack_i32(len(buf) + 1) + buf + ZERO


def uuid2bson(val: UUID) -> Tuple[bytes, bytes]:
    """Encode uuid as BSON Binary / UUID."""
    assert isinstance(val, UUID)
    bval = val.bytes
    return BSON_BINARY, pack_i32(len(bval)) + BSON_BINARY_UUID + bval


_dflt_encoder_map = {bool: bool2bson,
                     bytearray: bytes2bson,
                     bytes: bytes2bson,
                     datetime: datetime2bson,
                     Decimal: decimal2bson,
                     float: float2bson,
                     int: int2bson,
                     type(None): none2bson,
                     str: string2bson,
                     UUID: uuid2bson
                     }                          # type: EncodeFunctionMap


class BSONEncoder:

    mode = 'b'

    def __init__(self, encoders: EncodeFunctionMap = None,
                 transformers: Iterable[TransformFunction] = None) -> None:
        encoder_map = {}                        # type: EncodeFunctionMap
        if encoders:
            encoder_map.update(encoders)
        self._encoder_map = encoder_map
        self._transformers = transformers or []

    def _get_encoder(self, obj: object):
        obj_type = type(obj)
        try:
            return self._encoder_map[obj_type]
        except KeyError:
            return _dflt_encoder_map[obj_type]      # type: EncodeFunction

    def encode(self, obj: object, stream: ByteStream) -> int:
        """Encode obj as BSON document and write it to stream."""
        if isinstance(obj, (list, tuple)):
            raise TypeError("BSON array must be embedded in a document.")
        code, chunk = self._encode_obj(obj)
        return stream.write(chunk)

    def _encode_obj(self, obj: object) -> Tuple[bytes, bytes]:
        if isinstance(obj, dict):
            return BSON_DOCUMENT, self._encode_elems(obj.items())
        if isinstance(obj, (list, tuple)):
            return BSON_ARRAY, self._encode_elems(enumerate(obj))
        try:
            encode = self._get_encoder(obj)
        except KeyError:
            pass
        else:
            return encode(obj)
        for transform in self._transformers:
            trans_obj = transform(obj)
            if trans_obj is not None:
                return self._encode_obj(trans_obj)
        raise ValueError("Unable to encode instance of %s" % type(obj))

    def _encode_elems(self, elems: Iterable[Tuple[Union[int, str], object]]) \
            -> bytes:
        chunks = []
        for key, val in elems:
            name = str(key).encode('utf8') + ZERO
            code, chunk = self._encode_obj(val)
            chunks.append(code + name + chunk)
        length = sum([len(chunk) for chunk in chunks]) + 5
        return pack('<i', length) + b''.join(chunks) + ZERO


def bson2bytes(bval: bytes) -> bytes:
    """Decode BSON Binary as bytes."""
    return bval


def bson2bool(bval: bytes) -> bool:
    """Decode BSON Boolean as bool."""
    return bool(ord(bval))


def bson2datetime(bval: bytes) -> datetime:
    """Decode BSON UTC datetime as datetime."""
    # BSON datetime is milliseconds since the epoch
    t = unpack('<q', bval)[0] / 1000.
    dt = timestamp2datetime(t)
    # round microseconds to milliseconds and set timezone to UTC
    ms = int(round(dt.microsecond, -3))
    dt = dt.replace(microsecond=ms, tzinfo=UTC())
    return dt


def bson2decimal(bval: bytes) -> Decimal:
    """Decode BSON Binary / Custom as Decimal or int."""
    sign, exp = unpack('<Bb', bval[:2])
    buf = bval[2:]
    chunks = unpack('<' + 'B' * len(buf), buf)
    mant = 0
    for i in chunks:
        mant = mant << 8
        mant += i
    if exp < 0:
        return (-1) ** sign * Decimal(mant) * Decimal(10) ** exp
    # we have an int
    return (-1) ** sign * mant * 10 ** exp


def bson2float(bval: bytes) -> float:
    """Decode BSON double as float."""
    return unpack('<d', bval)[0]


def bson2int(bval: bytes) -> int:
    """Decode BSON int32 or int64 as integer."""
    try:
        return unpack('<q', bval)[0]
    except StructError:
        return unpack('<i', bval)[0]


def bson2none(bval: bytes) -> None:
    """Decode BSON NULL as None."""
    return None


def bson2string(bval: bytes) -> str:
    """Decode BSON UTF-8 string as string."""
    return bval.decode('utf8')


def bson2uuid(bval: bytes) -> UUID:
    """Decode BSON Binary UUID as UUID."""
    return UUID(bytes=bval)


_dflt_decoder_map = {BSON_BOOLEAN: bson2bool,
                     BSON_BINARY + BSON_BINARY_GENERIC: bson2bytes,
                     BSON_BINARY + BSON_BINARY_UUID: bson2uuid,
                     BSON_BINARY + BSON_BINARY_CUSTOM: bson2decimal,
                     BSON_DATETIME: bson2datetime,
                     BSON_FLOAT: bson2float,
                     BSON_INT32: bson2int,
                     BSON_INT64: bson2int,
                     BSON_NULL: bson2none,
                     BSON_STRING: bson2string
                     }                          # type: DecodeFunctionMap


def check_end_zero(buf: bytes) -> None:
    """Raise ValueError if buf[-1:] != 0x00"""
    if buf[-1:] != ZERO:
        raise ValueError("Invalid BSON document.")


class BSONDecoder:

    mode = 'b'

    def __init__(self, decoders: DecodeFunctionMap = None,
                 recreators: List[RecreateFunction] = None) -> None:
        decoder_map = {}                # type: DecodeFunctionMap
        if decoders:
            decoder_map.update(decoders)
        # add the recursive decoders for embeded docs and arrays
        decoder_map[BSON_DOCUMENT] = self._decode_obj
        decoder_map[BSON_ARRAY] = self._decode_array
        # add forwarder to binary subtype decoders
        decoder_map[BSON_BINARY] = self._decode_binary
        self._decoder_map = decoder_map
        self._recreators = recreators or []

    def _get_parser(self, code: bytes) \
            -> Callable[['BSONDecoder', bytes], Tuple[bytes, bytes]]:
        try:
            return self._parser_map[code]
        except KeyError:
            raise ValueError("BSON element '%s' not supported." % repr(code))

    def _get_decoder(self, code: bytes) -> DecodeFunction:
        try:
            return self._decoder_map[code]
        except KeyError:
            return _dflt_decoder_map[code]      # type: DecodeFunction

    def decode(self, stream: ByteStream) -> object:
        """Read BSON document from stream and return reconstructed object."""
        buf = stream.read(4)
        nbytes = unpack_i32(buf[:4])
        buf = stream.read(nbytes - 4)
        check_end_zero(buf)
        return self._decode_obj(buf[:-1])

    def _decode_obj(self, buf: bytes) -> object:
        obj = {}                    # type: Dict[str, object]
        obj.update(self._decode_elems(buf))
        for recreator in self._recreators:
            recr_obj = recreator(obj)
            if recr_obj:
                return recr_obj
        return obj

    def _decode_array(self, buf: bytes) -> List:
        return [val for idx, val in self._decode_elems(buf)]

    def _decode_binary(self, buf: bytes) -> object:
        subtype = buf[:1]
        code = BSON_BINARY + subtype
        try:
            decode = self._get_decoder(code)
        except:
            # no decoder registered for this subtype
            raise ValueError("BSON element '%s' not supported." % repr(code))
        else:
            return decode(buf[1:])

    def _decode_elems(self, buf: bytes) \
            -> Generator[Tuple[str, object], None, None]:
        buf = buf[:]
        while len(buf) > 0:
            code = buf[:1]
            name, buf = self._parse_cstr(buf[1:])
            parse = self._get_parser(code)
            # _get_parser returns unbound methods, so self as param is needed:
            bval, buf = parse(self, buf)
            decode = self._get_decoder(code)
            val = decode(bval)
            yield name, val

    def _parse_cstr(self, buf: bytes) -> Tuple[str, bytes]:
        idx = buf.find(ZERO)
        return buf[:idx].decode('utf8'), buf[idx + 1:]

    def _parse_fixed_length(self, buf: bytes, nbytes: int = 0) \
            -> Tuple[bytes, bytes]:
        return buf[:nbytes], buf[nbytes:]

    def _parse_string(self, buf: bytes) -> Tuple[bytes, bytes]:
        nbytes = unpack_i32(buf[:4])
        idx_rem_buf = nbytes + 4
        bval = buf[4:idx_rem_buf]
        check_end_zero(bval)
        return bval[:-1], buf[idx_rem_buf:]

    def _parse_binary(self, buf: bytes) -> Tuple[bytes, bytes]:
        nbytes = unpack_i32(buf[:4])
        idx_rem_buf = nbytes + 5
        bval = buf[4:idx_rem_buf]
        return bval, buf[idx_rem_buf:]

    def _parse_embedded_doc(self, buf: bytes) -> Tuple[bytes, bytes]:
        nbytes = unpack_i32(buf[:4])
        bval = buf[4:nbytes]
        check_end_zero(bval)
        return bval[:-1], buf[nbytes:]

    _parser_map = {BSON_ARRAY: _parse_embedded_doc,
                   BSON_BINARY: _parse_binary,
                   BSON_BOOLEAN: partial(_parse_fixed_length, nbytes=1),
                   BSON_DATETIME: partial(_parse_fixed_length, nbytes=8),
                   BSON_DOCUMENT: _parse_embedded_doc,
                   BSON_FLOAT: partial(_parse_fixed_length, nbytes=8),
                   BSON_INT32: partial(_parse_fixed_length, nbytes=4),
                   BSON_INT64: partial(_parse_fixed_length, nbytes=8),
                   BSON_NULL: partial(_parse_fixed_length, nbytes=0),
                   BSON_STRING: _parse_string}


def dump(obj, stream: ByteStream) -> int:
    """Encode obj as BSON document and write it to stream."""
    encoder = BSONEncoder()
    return encoder.encode(obj, stream)


def dumps(obj: object) -> bytes:
    """Return BSON representation of `obj`."""
    buf = BytesIO()
    dump(obj, buf)
    return buf.getvalue()


def load(stream: ByteStream) -> object:
    """Read BSON document from `stream` and return reconstructed object."""
    decoder = BSONDecoder()
    return decoder.decode(stream)


def loads(bson: bytes) -> object:
    """Reconstruct object from BSON document `bson`."""
    buf = BytesIO(bson)
    return load(buf)
