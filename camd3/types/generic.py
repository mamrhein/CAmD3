# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        generic
# Purpose:     Generic types
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


"""Generic types"""


from abc import abstractmethod
from io import BytesIO, StringIO
from typing import AnyStr, Generic


class Stream(Generic[AnyStr]):

    @abstractmethod
    def read(self, n: int = -1) -> AnyStr:
        """Read at most `n` characters from stream."""

    @abstractmethod
    def write(self, s: AnyStr) -> int:
        """Write `s` to stream."""


ByteStream = Stream[bytes]
ByteStream.register(BytesIO)

CharStream = Stream[str]
CharStream.register(StringIO)


__all__ = [
    'ByteStream',
    'CharStream',
    'Stream',
]
