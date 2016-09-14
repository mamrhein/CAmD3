# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        attribute
# Purpose:     Descriptors for defining attributes
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


"""Descriptors for defining attributes"""


from keyword import iskeyword
from typing import Any, Callable, Iterable, Optional, Text, Tuple, Union
from typing import cast
from .immutable import Immutable

# some types used in type hints
ConverterType = Callable[[Any], Any]
ConstraintType = Callable[[Any], bool]
ContraintsParamType = Union[ConstraintType, Iterable[ConstraintType], None]
BoundContraintsType = Tuple[ConstraintType, ...]

# value used to represent an absent default
_NODEFAULT = object()


def is_identifier(s: str) -> bool:
    """Return True if `s` is a valid identifier (and not a keyword)."""
    try:
        return s.isidentifier() and not iskeyword(s)
    except AttributeError:
        return False


class Attribute:

    """Descriptor class for defining attributes of objects."""

    __slots__ = ('_name', '_priv_member', '_immutable', '_default',
                 '_converter', '_constraints', '_bound_constraints', '_doc')

    def __init__(self, immutable: bool = False, default: Any = _NODEFAULT,
                 converter: Optional[ConverterType] = None,
                 constraints: ContraintsParamType = None,
                 doc: Optional[Text] = None) -> None:
        """Initialze attribute."""
        assert isinstance(immutable, bool), \
            "Argument 'immutable' must be of type 'bool'."
        self._immutable = immutable
        self._default = default
        assert converter is None or callable(converter), \
            "Argument 'converter' must be callable."
        self._converter = converter
        self._constraints = constraints
        if constraints is None:
            self._bound_constraints = ()    # type: BoundContraintsType
        elif callable(constraints):         # a single callable?
            self._bound_constraints = (self._bind_constraint(
                                       cast(ConstraintType, constraints)),)
        else:                               # an iterable of callables
            try:
                it = iter(cast(Iterable[ConstraintType], constraints))
            except TypeError:
                it = None
            assert it and all(callable(item) for item in it), \
                "Argument 'constraints' must be a single callable or an " \
                "iterable of callables."
            self._bound_constraints = tuple((self._bind_constraint(func)
                                             for func
                                             in cast(Iterable[ConstraintType],
                                                     constraints)))
        self._doc = doc

    def _bind_constraint(self, func: Callable[[Any], bool]) \
            -> Callable[[Any], bool]:
        def check(attr_value: Any) -> bool:
            if not func(attr_value):
                if func.__doc__:
                    msg = func.__doc__.format(self.name)
                else:
                    msg = "Invalid value given for attribute '{}'.".format(
                          self.name)
                raise ValueError(msg)
        return check

    @property
    def name(self):
        """Name of the attribute."""
        return self._name               # type: str

    def __set_name__(self, name: str) -> None:
        try:
            my_name = self.name
        except AttributeError:
            if is_identifier(name):
                self._name = name
                if name.startswith('_'):
                    self._priv_member = name + '_'
                else:
                    self._priv_member = '_' + name
                return
        else:
            if my_name != name:
                raise AttributeError("Can't change name of attribute.")
        # name is not valid
        raise ValueError("'{}' is not a valid identifier.".format(str(name)))

    @property
    def immutable(self) -> bool:
        "Return True if attribute can't be modified, otherwise False."
        return self._immutable

    @property
    def default(self):
        """Value or callable used to obtain a default value for the attribute.
        """
        return self._default

    @property
    def converter(self) -> ConverterType:
        """Callable used to adapt the value given in an assignment to the
        attribute."""
        return self._converter

    @property
    def constraints(self) -> ContraintsParamType:
        """Callable(s) used to check the value given in an assignment to the
        attribute."""
        return self._constraints

    def __get__(self, instance, owner):
        """Return value of managed attribute."""
        if instance is None:    # if accessed via class, return descriptor
            return self         # (i.e. self),
        else:                   # else return value of storage attribute ...
            try:
                return getattr(instance, self._priv_member)
            except AttributeError:
                pass
            default = self._default     # ... or default
            if default is _NODEFAULT:
                raise AttributeError("Unassigned attribute '{}'."
                                     .format(self._name))
            if callable(default):
                return default(instance)
            else:
                return default

    def __set__(self, instance, value):
        """Set value of managed attribute."""
        try:
            getattr(instance, self._priv_member)
        except AttributeError:
            pass        # fall through
        else:
            if self._immutable or isinstance(instance, Immutable):
                raise AttributeError("Can't set immutable attribute '{}'."
                                     .format(self._name))
        try:
            value = self._converter(value)
        except TypeError:
            if self._converter is not None:
                raise
        for check in self._bound_constraints:
            check(value)
        setattr(instance, self._priv_member, value)

    def __delete__(self, instance):
        """Remove value of managed attribute."""
        if self._immutable or isinstance(instance, Immutable):
            raise AttributeError("Can't delete immutable attribute '{}'."
                                 .format(self._name))
        try:
            delattr(instance, self._priv_member)
        except AttributeError:
            pass

    @property
    def __doc__(self):
        return self._doc


class AbstractAttribute(Attribute):

    """Descriptor class for defining abstract attributes of objects."""

    __isabstractmethod__ = True


# TODO: MultiValueAttribute, QualifiedMultiValueAttribute

__all__ = [
    'AbstractAttribute',
    'Attribute',
]
