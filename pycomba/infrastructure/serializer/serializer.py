# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        serializer
# Purpose:     Serialize and recreate objects
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

"""Serialize and recreate objects"""

import importlib
from io import BytesIO, StringIO
from typing import AnyStr, MutableMapping, Optional
from ..component import get_utility, implementer, ComponentLookupError
from . import EncoderFactory, Serializer
from . import DecoderFactory, Deserializer
from . import State
from ...types.generic import Stream


IO_MODE_MAP = {'t': StringIO,
               'b': BytesIO}


@implementer(Serializer)
class Serializer_:

    """A Serializer writes objects to a stream, using the encoder registered
    for the specific format given to the serializers factory."""

    @staticmethod
    def transform(obj: object) -> Optional[MutableMapping]:
        """Transform `obj` into a serializable form."""
        if isinstance(obj, type):
            return None                 # can't transform a class
        try:
            reduced_obj = obj.__reduce__()
        except (AttributeError, TypeError):
            pass
        else:
            if len(reduced_obj) == 2:
                # we only use this form if a call to a factory function is
                # sufficient, i.e. no additional state must be set
                cls, clsargs = reduced_obj
                full_cls_name = '.'.join((cls.__module__, cls.__name__))
                return {'__class__': full_cls_name,
                        '__clsargs__': clsargs}
        try:
            state = State[obj].get_state()
        except TypeError:
            # unable to retrieve state
            return None
        cls = type(obj)
        full_cls_name = '.'.join((cls.__module__, cls.__name__))
        try:
            state['__class__'] = full_cls_name
        except TypeError:
            state = {'__class__': full_cls_name,
                     '__state__': state}
        return state

    def __init__(self, format: str) -> None:
        """Create serializer that uses the encoder registered for `format`."""
        try:
            encoder_factory = get_utility(EncoderFactory, name=format)
        except ComponentLookupError:
            pass
        else:
            self._encoder = encoder_factory(transformers=[self.transform])
            return
        raise ValueError("No encoder factory registered for format '%s'."
                         % format)

    @property
    def mode(self) -> str:
        return self._encoder.mode

    def dump(self, obj: object, stream: Stream) -> int:
        """Write a serialized representation of `obj` to `stream`."""
        self._encoder.encode(obj, stream)

    def dumps(self, obj: object) -> AnyStr:
        """Return a serialized representation of `obj` as string or byte
        array."""
        buf = IO_MODE_MAP[self._encoder.mode]()
        self.dump(obj, buf)
        return buf.getvalue()


@implementer(Deserializer)
class Deserializer_:

    """A Deserializer reads a serialized representation of an object from a
    stream and recreates the object."""

    @staticmethod
    def recreate(obj_repr: MutableMapping) -> object:
        """Recreate object from `obj_repr`."""
        try:
            full_cls_name = obj_repr['__class__']
        except KeyError:
            return None
        mod_name, cls_name = full_cls_name.rsplit('.', 1)
        mod = importlib.import_module(mod_name)
        cls = mod.__dict__[cls_name]
        try:
            clsargs = obj_repr['__clsargs__']
        except KeyError:
            pass
        else:
            return cls(*clsargs)
        try:
            state = obj_repr['__state__']
        except KeyError:
            del obj_repr['__class__']
            state = obj_repr
        obj = object.__new__(cls)
        State[obj].set_state(state)
        return obj

    def __init__(self, format: str) -> None:
        """Create deserializer that uses the decoder registered for `format`.
        """
        try:
            decoder_factory = get_utility(DecoderFactory, format)
        except ComponentLookupError:
            pass
        else:
            self._decoder = decoder_factory(recreators=[self.recreate])
            return
        raise ValueError("No decoder factory registered for format '%s'."
                         % format)

    @property
    def mode(self) -> str:
        return self._decoder.mode

    def load(self, stream: Stream) -> object:
        """Read a serialized object representation from the stream given to
        the deserializer and return the reconstituted object hierarchy
        specified therein, using the given decoder."""
        return self._decoder.decode(stream)

    def loads(self, obj_repr: AnyStr) -> object:
        """Return the object reconstituted from the encoded representation in
        `obj_repr`."""
        buf = IO_MODE_MAP[self._decoder.mode](obj_repr)
        return self.load(buf)
