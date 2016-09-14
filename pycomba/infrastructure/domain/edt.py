# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        edt
# Purpose:     Enumerated Datatypes
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


"""Enumerated Datatypes"""


from enum import Enum, EnumMeta
from typing import Any, Dict, Iterable, MutableMapping, Tuple, TypeVar, Union
from . import Entity
from ..component import Attribute
from ..component.component import ComponentMeta
#from ...gbbs.tools import copydoc


EnumType = TypeVar('EnumType', bound=Enum)


class EDTMeta(ComponentMeta):

    def __new__(metacls, cls_name: str, bases: Tuple[type, ...],
                namespace: MutableMapping[str, Any],
                **kwds: Any) -> 'EDTMeta':
        for base in bases:
            if base is not EDT and issubclass(base, EDT):
                raise TypeError("Can't extend EDTs.")
        namespace['_instance_map'] = {}
        enum = kwds.pop('enum')             # type: EnumMeta
        assert issubclass(enum, Enum), "'enum' must be a subclass of Enum."
        namespace['_enum'] = enum
        namespace['_sealed'] = False
        return super().__new__(metacls, cls_name, bases, namespace, **kwds)

    def __len__(cls) -> int:
        return len(cls._instance_map)

    def __contains__(cls, inst: Any) -> bool:
        return type(inst) is cls

    def __getitem__(cls, id):
        return cls._instance_map[id]

    def __iter__(cls):
        return (cls._instance_map[id] for id in cls._enum)

    def __call__(cls, *args, **kwds):
        if cls._sealed:
            raise TypeError("Can't create new members of %r." % cls)
        inst = super().__call__(*args, **kwds)
        cls._instance_map[inst.id] = inst

    @property
    def enum(cls) -> EnumMeta:
        return cls._enum                    # type: EnumMeta

    def populate(cls, src: Union[Iterable, Dict], complete: bool = True) \
            -> None:
        if isinstance(src, Dict):
            cls._populate_from_dict(src)
        else:
            cls._populate_from_iterable(src)
        cls._sealed = complete

    def _populate_from_iterable(cls, it: Iterable) -> None:
        for id, *args in it:
            cls(id, *args)

    def _populate_from_dict(cls, dict_: Dict) -> None:
        for id, args in dict_.items():
            cls(id, *args)


class EDT(Entity, metaclass=EDTMeta, enum=Enum):

    id = Attribute(immutable=True, doc=Entity.id.__doc__)

    def __init__(self, id: EnumType, *args, **kwds) -> None:
        try:
            self.__class__[id]
        except KeyError:
            pass
        else:
            raise ValueError("Duplicate id: %r" % id)
        self.id = id
        for idx, name in enumerate(self.__class__.attr_names):
            self.__setattr__(name, args[idx])

    @property
    def name(self):
        return self._id.name

    @property
    def code(self):
        return self._id.value

    def __repr__(self) -> str:
        """repr(self)"""
        cls = self.__class__
        return "%s[%s(%r)]" % (cls.__name__, cls.enum.__name__, self.code)
