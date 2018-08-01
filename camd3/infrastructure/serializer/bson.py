# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        bson
# Purpose:     BSON encoder / decoder (interface wrapper for gbbs.bson)
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


"""BSON encoder / decoder (interface wrapper for gbbs.bson)"""


from struct import pack, unpack
from struct import error as StructError
from typing import (Any, Callable, Dict, Iterable, List, Tuple, Union)
from decimalfp import Decimal
from .. import implementer
from ...gbbs.bson import (BSONEncoder, BSONDecoder,
                          BSON_BINARY, BSON_BINARY_CUSTOM)
from . import Encoder, EncoderFactory, Decoder, DecoderFactory


# some types
EncodeFunction = Callable[[object], Tuple[bytes, bytes]]
EncodeFunctionMap = Dict[type, EncodeFunction]
TransformFunction = Callable[[object], object]
DecodeFunction = Callable[[bytes], object]
DecodeFunctionMap = Dict[Any, DecodeFunction]
RecreateFunction = Callable[[Dict[str, object]], object]


# declare interfaces

implementer(BSONEncoder, Encoder)
implementer(BSONDecoder, Decoder)


# BSON encoder factory

def decimal2bson(val: Decimal) -> Tuple[bytes, bytes]:
    """Encode Decimal as BSON Binary / Custom."""
    assert isinstance(val, Decimal)
    sign, mant, exp = val.as_tuple()
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
    return BSON_BINARY, pack('<i', len(buf)) + BSON_BINARY_CUSTOM + buf


@implementer(EncoderFactory)
class BSONEncoderFactory:

    """A BSONEncoderFactory creates encoders for the BSON format."""

    def __call__(self, encoders: EncodeFunctionMap = None,
                 transformers: Iterable[TransformFunction] = None) \
            -> BSONEncoder:
        encoder_map = {Decimal: decimal2bson}
        if encoders:
            encoder_map.update(encoders)
        return BSONEncoder(encoders=encoder_map, transformers=transformers)


# BSON decoder factory

def bson2decimal(bval: bytes) -> Union[Decimal, int]:
    """Decode BSON Binary / Custom as Decimal."""
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


@implementer(DecoderFactory)
class BSONDecoderFactory:

    """A BSONDecoderFactory creates decoders for the BSON format."""

    def __call__(self, decoders: DecodeFunctionMap = None,
                 recreators: List[RecreateFunction] = None) -> BSONDecoder:
        ext_decoders = {BSON_BINARY + BSON_BINARY_CUSTOM: bson2decimal}
        if decoders:
            ext_decoders.update(decoders)
        return BSONDecoder(decoders=ext_decoders, recreators=recreators)
