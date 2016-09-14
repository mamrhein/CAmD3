# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        serializer package
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

from abc import abstractmethod
from typing import Any, AnyStr, Callable, Iterable, List, Mapping, Union
from .state import State, StateAdapter
from ..component import Attribute, Component
from ...types.generic import Stream


# some types
EncodeFunction = Callable[[object], AnyStr]
EncodeFunctionMap = Mapping[type, EncodeFunction]
TransformFunction = Callable[[object], object]
DecodeFunction = Callable[[AnyStr], object]
DecodeFunctionMap = Mapping[Any, Union[DecodeFunction, List[DecodeFunction]]]
RecreateFunction = Callable[[Mapping[str, object]], object]


class Encoder(Component):

    """An Encoder encodes objects to a stream, using a specific format."""

    mode = Attribute(immutable=True,
                     doc="Type of stream ('t' = text, 'b' = binary)")

    @abstractmethod
    def encode(self, obj: object, stream: Stream) -> int:
        """Encode obj in specific format and write it to stream.

        Args:
            obj (object): the object to be encoded
            stream (<file-like object>): stream to which encoded
                representation of `obj` is written

        Returns:
            int: the number of characters / bytes written

        Raises:
            ValueError: unable to encode `obj`
        """


class EncoderFactory(Component):

    """An EncoderFactory creates encoders for a specific format."""

    @abstractmethod
    def __call__(self, encoders: EncodeFunctionMap = None,
                 transformers: Iterable[TransformFunction] = None) -> Encoder:
        """Return an encoder (providing interface :class:`Encoder`).

        Args:
            encoders (dict): an optional mapping, which maps types to
                callables that are used to encode objects of the
                corresponding type
            transformers (list): an optional list of callables that are used
                to transform instances of types unknown to the encoder to
                instances of known types

        Returns:
            Encoder: instance of :class:`Encoder`
        """


class Decoder(Component):

    """A Decoder decodes objects from a stream, using a specific format."""

    mode = Attribute(immutable=True,
                     doc="Type of stream ('t' = text, 'b' = binary)")

    @abstractmethod
    def decode(self, stream: Stream) -> object:
        """Read encoded representation from stream and return reconstructed
        object.

        Args:
            stream (<file-like object>): stream from which encoded
                representation of `obj` is read

        Returns:
            object: the reconstructed object
        """


class DecoderFactory(Component):

    """A DecoderFactory creates decoders for a specific format."""

    @abstractmethod
    def __call__(self, decoders: DecodeFunctionMap = None,
                 recreators: List[RecreateFunction] = None) -> Decoder:
        """Return a decoder (providing interface :class:`Decoder`).

        Keyword Args:
            decoders (dict): an optional mapping, which maps type codes to
                callables that are used to decode object representations
                denoted by the corresponding type code
            recreators (list): an optional list of callables that are used
                to recreate instances from the decoded representation

        Returns:
            Decoder: instance of :class:`Decoder`
        """


class Serializer(Component):

    """A Serializer writes objects to a stream, using the encoder registered
    for the specific format given to the serializers factory."""

    @abstractmethod
    def dump(self, obj: object, stream: Stream) -> int:
        """Write a serialized representation of `obj` to `stream`.

        Args:
            obj (object): the object to be serialized
            stream (<file-like object>): stream to which encoded
                representation of `obj` is written

        Returns:
            int: the number of characters / bytes written
        """

    @abstractmethod
    def dumps(self, obj: object) -> AnyStr:
        """Return a serialized representation of `obj` as byte array.

        Args:
            obj (object): the object to be serialized

        Returns:
            AnyStr: serialized representation of `obj`, according
                to `format` given to serializers factory
        """


class SerializerFactory(Component):

    """A SerializerFactory creates serializers for a specific format."""

    @abstractmethod
    def __call__(format: str) -> Serializer:
        """Create serializer that uses the encoder registered for `format`.

        Args:
            format (str): name of the format to be used

        Returns:
            Serializer: instance of :class:`Serializer`

        Raises:
            ValueError: no encoder registered for the given `format`
        """


class Deserializer(Component):

    """A Deserializer reads objects from a stream using the decoder registered
    for the specific format given to the deserializers factory."""

    @abstractmethod
    def load(self, stream: Stream) -> object:
        """Return the object reconstituted from the encoded representation
        read from `stream`.

        Args:
            stream (<file-like object>): stream from which encoded
                representation is read

        Returns:
            object: the reconstituted object
        """

    @abstractmethod
    def loads(self, obj_repr: AnyStr) -> object:
        """Return the object reconstituted from the encoded representation in
        `obj_repr`.

        Args:
            AnyStr: encoded object representation

        Returns:
            object: the reconstituted object
        """


class DeserializerFactory(Component):

    """A DeserializerFactory creates deserializers for a specific format."""

    @abstractmethod
    def __call__(format: str) -> Deserializer:
        """Create deserializer that uses the decoder registered for `format`.

        Args:
            format (str): name of the format to be used

        Returns:
            Deserializer: instance of :class:`Deserializer`

        Raises:
            ValueError: no decoder registered for the given `format`
        """

__all__ = [
    'Decoder',
    'DecoderFactory',
    'Encoder',
    'EncoderFactory',
    'State',
    'StateAdapter',
]
