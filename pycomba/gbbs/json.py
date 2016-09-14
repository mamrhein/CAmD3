# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        json
# Purpose:     Simple JSON encoder / decoder
#
# Author:      Michael Amrhein (michael@adrhinum.de)
#
# Copyright:   (c) 2013 Michael Amrhein
# License:     This program is part of a larger application. For license
#              details please read the file LICENSE.TXT provided together
#              with the application.
# ----------------------------------------------------------------------------
# $Source$
# $Revision$


"""Simple JSON encoder / decoder.

This module provides classes and functions which can be used to serialize
native Python objects to or recreate them from JSON documents.
"""


import json
from datetime import date, datetime, time
from decimal import Decimal
from io import StringIO
from numbers import Number
from typing import (Callable, Dict, Iterable, List, Optional, Union)
from uuid import UUID
from ..types.generic import CharStream

strptime = datetime.strptime


# some types
EncodeFunction = Callable[[object], Union[str, float]]
EncodeFunctionMap = Dict[type, EncodeFunction]
TransformFunction = Callable[[object], object]
DecodeFunction = Callable[[str], object]
DecodeFunctionList = List[DecodeFunction]
RecreateFunction = Callable[[Dict[str, object]], object]


ISO_DATE_FORMAT = "%Y-%m-%d"
NAIVE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
TZ_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
NAIVE_TIME_FORMAT = "%H:%M:%SZ"
TZ_TIME_FORMAT = "%H:%M:%S%z"


def date2json(d: date) -> str:
    """Encode date as JSON string, in ISO format (i.e. '%Y-%m-%d')."""
    assert isinstance(d, date)
    return d.isoformat()


def datetime2json(dt: datetime) -> str:
    """Encode datetime as JSON string according to ECMA-262."""
    assert isinstance(dt, datetime)
    if dt.tzinfo:
        fm = TZ_DATETIME_FORMAT
    else:
        fm = NAIVE_DATETIME_FORMAT
    return format(dt, fm)


def time2json(t: time) -> str:
    """Encode time as JSON string according to ECMA-262."""
    assert isinstance(t, time)
    if t.tzinfo:
        fm = TZ_TIME_FORMAT
    else:
        fm = NAIVE_TIME_FORMAT
    return format(t, fm)


# work around to make json.JSONEncoder encode Decimal as JSON number
class _number_str(float):

    def __init__(self, val: Decimal) -> None:
        self.val = val

    def __repr__(self) -> str:
        return str(self.val)


def decimal2json(val: Decimal) -> float:
    """Encode Decimal as JSON number."""
    assert isinstance(val, Decimal)
    return _number_str(val)


def uuid2json(val: UUID) -> str:
    """Encode uuid as JSON string."""
    assert isinstance(val, UUID)
    return str(val)


_ext_encoder_map = {date: date2json,
                    datetime: datetime2json,
                    time: time2json,
                    Decimal: decimal2json,
                    UUID: uuid2json
                    }                           # type: EncodeFunctionMap


class JSONEncoder:

    mode = 't'

    def __init__(self, encoders: EncodeFunctionMap = None,
                 transformers: Iterable[TransformFunction] = None) -> None:
        self._encoder_map = _ext_encoder_map
        if encoders:
            self._encoder_map.update(encoders)
        self._transformers = transformers or []
        self._json_encoder = json.JSONEncoder(ensure_ascii=False,
                                              allow_nan=False,
                                              default=self._encode_obj)

    def encode(self, obj: object, stream: CharStream) -> int:
        """Encode obj as JSON document and write it to stream."""
        json_encoder = self._json_encoder
        n_chars = 0
        for chunk in json_encoder.iterencode(obj):
            n_chars += stream.write(str(chunk))
        return n_chars

    def _encode_obj(self, obj: object) -> object:
        obj_type = type(obj)
        try:
            encode = self._encoder_map[obj_type]
        except KeyError:
            pass
        else:
            return encode(obj)
        for transform in self._transformers:
            trans_obj = transform(obj)
            if trans_obj is not None:
                return trans_obj
        raise ValueError("Unable to encode instance of %s" % type(obj))


def json2date(jsonRepr: str) -> Optional[date]:
    """Decode JSON date string as date."""
    try:
        return strptime(jsonRepr, ISO_DATE_FORMAT).date()
    except:
        return None


def json2datetime(jsonRepr: str) -> Optional[datetime]:
    """Decode JSON datetime string according to ECMA-262 as datetime."""
    try:
        return strptime(jsonRepr, NAIVE_DATETIME_FORMAT)
    except:
        pass
    try:
        return strptime(jsonRepr, TZ_DATETIME_FORMAT)
    except:
        pass
    return None


def json2time(jsonRepr: str) -> Optional[time]:
    """Decode JSON time string according to ECMA-262 as time."""
    try:
        return strptime(jsonRepr, NAIVE_TIME_FORMAT).time()
    except:
        pass
    try:
        return strptime(jsonRepr, TZ_TIME_FORMAT).timetz()
    except:
        pass
    return None


def json2uuid(jsonRepr: str) -> Optional[UUID]:
    """Decode JSON string as UUID."""
    try:
        return UUID(jsonRepr)
    except:
        return None


_str_decoders = [json2uuid,
                 json2date,
                 json2datetime,
                 json2time
                 ]                          # type: DecodeFunctionList


class JSONDecoder:

    mode = 't'

    def __init__(self, number: Callable[[str], Number] = Decimal,
                 str_decoders: DecodeFunctionList = None,
                 recreators: List[RecreateFunction] = None) -> None:
        if str_decoders:
            self._str_decoders = str_decoders + _str_decoders
        else:
            self._str_decoders = _str_decoders
        self._recreators = recreators or []
        self._jsonDecoder = json.JSONDecoder(object_hook=self._hook,
                                             parse_float=number)

    def _decode_str(self, val: str) -> object:
        for decoder in self._str_decoders:
            newVal = decoder(val)
            if newVal is not None:
                return newVal
        return None

    def _hook(self, dict_: Dict[str, Union[object, List]]) -> object:
        for key, val in dict_.items():
            if isinstance(val, str):
                newVal = self._decode_str(val)
                if newVal is not None:
                    dict_[key] = newVal
            elif isinstance(val, list):
                for idx, item in enumerate(val):
                    if isinstance(item, str):
                        newVal = self._decode_str(item)
                        if newVal is not None:
                            val[idx] = newVal
        for recreator in self._recreators:
            recr_obj = recreator(dict_)
            if recr_obj:
                return recr_obj
        return dict_

    def decode(self, stream: CharStream) -> object:
        """Read JSON document from stream and return reconstructed object."""
        return self._jsonDecoder.decode(stream.read())


def dump(obj: object, stream: CharStream) -> int:
    """Encode `obj` as JSON document and write it to `stream`."""
    encoder = JSONEncoder()
    return encoder.encode(obj, stream)


def dumps(obj: object) -> str:
    """Return JSON representation of `obj` as string."""
    buf = StringIO()
    dump(obj, buf)
    return buf.getvalue()


def load(stream: CharStream) -> object:
    """Read JSON document from stream and return reconstructed object."""
    decoder = JSONDecoder()
    return decoder.decode(stream)


def loads(jsonDoc: str) -> object:
    """Reconstruct object from JSON document (string)."""
    buf = StringIO(jsonDoc)
    return load(buf)
