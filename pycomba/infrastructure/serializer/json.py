# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        json
# Purpose:     JSON encoder / decoder (interface wrapper for gbbs.json)
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


"""JSON encoder / decoder (interface wrapper for gbbs.json)"""


from typing import Any, Callable, Dict, Iterable, List, Union
from decimalfp import Decimal
from .. import implementer
from ...gbbs.json import JSONEncoder, JSONDecoder
from . import Encoder, EncoderFactory, Decoder, DecoderFactory


# some types
EncodeFunction = Callable[[object], Union[str, float]]
EncodeFunctionMap = Dict[type, EncodeFunction]
TransformFunction = Callable[[object], object]
DecodeFunction = Callable[[str], object]
DecodeFunctionMap = Dict[Any, Union[DecodeFunction, List[DecodeFunction]]]
RecreateFunction = Callable[[Dict[str, object]], object]


# declare interfaces

implementer(JSONEncoder, Encoder)
implementer(JSONDecoder, Decoder)


# JSON encoder factory

# work around to make JSONEncoder encode Decimal as JSON number
class _number_str(float):

    def __init__(self, val: Decimal) -> None:
        self.val = val

    def __repr__(self) -> str:
        return str(self.val)


# encoder for type Decimal provided by pycomba
def decimal2json(val: Decimal) -> float:
    """Encode Decimal as JSON number."""
    assert isinstance(val, Decimal)
    return _number_str(val)


@implementer(EncoderFactory)
class JSONEncoderFactory:

    """A JSONEncoderFactory creates encoders for the JSON format."""

    def __call__(self, encoders: EncodeFunctionMap = None,
                 transformers: Iterable[TransformFunction] = None) \
            -> JSONEncoder:
        """Return a JSON encoder (providing interface :class:`Encoder`)."""
        ext_encoder_map = {Decimal: decimal2json}   # type: EncodeFunctionMap
        if encoders:
            ext_encoder_map.update(encoders)
        return JSONEncoder(encoders=ext_encoder_map,
                           transformers=transformers)


# JSON decoder factory

@implementer(DecoderFactory)
class JSONDecoderFactory:

    """A JSONDecoderFactory creates decoders for the JSON format."""

    def __call__(self, decoders: DecodeFunctionMap = None,
                 recreators: List[RecreateFunction] = None) -> JSONDecoder:
        """Return a JSON decoder (providing interface :class:`Decoder`)."""
        str_decoders = None
        if decoders:
            if len(decoders) == 1 and str in decoders:
                str_decoders = decoders[str]
                try:    # do we have an iterable?
                    iter(str_decoders)
                except TypeError:
                    str_decoders = [str_decoders]
            else:
                raise ValueError("JSONDecoder does not support extended "
                                 "decoders for types other than 'str'.")
        return JSONDecoder(str_decoders=str_decoders, recreators=recreators,
                           number=Decimal)
