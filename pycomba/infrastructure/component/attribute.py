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


from itertools import chain
from keyword import iskeyword
from typing import (Any, Callable, Iterable, Iterator, Mapping, Optional,
                    Text, Tuple, Union)
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

    def __init__(self, immutable: bool = False, default: Any = _NODEFAULT,
                 converter: Optional[ConverterType] = None,
                 constraints: ContraintsParamType = None,
                 doc: Optional[Text] = None) -> None:
        """Initialze attribute."""
        assert isinstance(immutable, bool), \
            "Argument 'immutable' must be of type 'bool'."
        self._immutable = immutable
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
        self.default = default
        self.__doc__ = doc

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
    def name(self) -> str:
        """Name of the attribute."""
        try:
            return self._name               # type: str
        except AttributeError:
            return '<unnamed>'

    def __set_name__(self, name: str) -> None:
        try:
            my_name = self._name
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
            return
        # name is not valid
        raise ValueError("'{}' is not a valid identifier.".format(str(name)))

    @property
    def immutable(self) -> bool:
        "Return True if attribute can't be modified, otherwise False."
        return self._immutable

    @property
    def converter(self) -> ConverterType:
        """Callable used to adapt the value given in an assignment to the
        attribute."""
        return self._converter

    @property
    def constraints(self) -> ContraintsParamType:
        """Callable(s) used to check the value(s) given in an assignment to
        the attribute."""
        return self._constraints

    def _check_immutable(self, instance: object) -> None:
        try:
            getattr(instance, self._priv_member)
        except AttributeError:
            pass        # fall through
        else:
            if self._immutable or isinstance(instance, Immutable):
                raise AttributeError("Can't modify immutable attribute '{}'."
                                     .format(self._name))

    def _convert_value(self, value: Any) -> Any:
        try:
            value = self._converter(value)
        except TypeError:
            if self._converter is not None:
                raise
        return value

    def _check_value(self, value: Any) -> Any:
        for check in self._bound_constraints:
            check(value)
        return value

    @property
    def default(self) -> Any:
        """Value or callable used to obtain a default value for the attribute.
        """
        return self._default

    @default.setter
    def default(self, default: Any) -> None:
        if default == _NODEFAULT or default is None:
            self._default = default
        elif callable(default):
            # wrap callable to convert and check default
            self._default = lambda instance: \
                self._check_value(self._convert_value(default(instance)))
        else:
            # convert and check default
            self._default = self._check_value(self._convert_value(default))

    def __get__(self, instance: Any, owner: type) -> Any:
        """Return value of managed attribute."""
        if instance is None:    # if accessed via class, return descriptor
            return self         # (i.e. self),
        else:                   # else return value of storage attribute ...
            try:
                return getattr(instance, self._priv_member)
            except AttributeError:
                pass
            default = self.default     # ... or default
            if default is _NODEFAULT:
                raise AttributeError("Unassigned attribute '{}'."
                                     .format(self._name))
            if callable(default):
                return default(instance)
            else:
                return default

    def __set__(self, instance: object, value: Any) -> None:
        """Set value of managed attribute."""
        self._check_immutable(instance)
        value = self._check_value(self._convert_value(value))
        setattr(instance, self._priv_member, value)

    def __delete__(self, instance: object) -> None:
        """Remove value of managed attribute."""
        if self._immutable or isinstance(instance, Immutable):
            raise AttributeError("Can't delete immutable attribute '{}'."
                                 .format(self._name))
        try:
            delattr(instance, self._priv_member)
        except AttributeError:
            pass


class AbstractAttribute(Attribute):

    """Descriptor class for defining abstract attributes of objects."""

    __isabstractmethod__ = True


def _check_instance(meth):
    def checker(self, *args, **kwds):
        if self._instance is None:
            raise AttributeError("Can't modify default value.")
        if self._immutable:
            raise AttributeError("Can't modify immutable attribute '{}'."
                                 .format(self._attr.name))
        return meth(self, *args, **kwds)
    checker.__doc__ = meth.__doc__
    return checker


def _convert_n_check_value(meth):
    def deco_meth(self, *args, **kwds):
        convert, check = (self._attr._convert_value, self._attr._check_value)
        args = [check(convert(value)) for value in args]
        return meth(self, *args, **kwds)
    deco_meth.__doc__ = meth.__doc__
    return deco_meth


def _convert_n_check_value_sets(meth):
    def deco_meth(self, *args, **kwds):
        convert, check = (self._attr._convert_value, self._attr._check_value)
        args = [(check(convert(value)) for value in chain(*args))]
        return meth(self, *args, **kwds)
    deco_meth.__doc__ = meth.__doc__
    return deco_meth


class _MultiValue(set):

    """Proxy for a set-like container, linked to an instance and an
    attriute of that instance"""

    def __init__(self, attr: Attribute, instance: Any = None,
                 values: Iterable[Any] = set()) -> None:
        self._attr = attr
        self._instance = instance
        self._immutable = attr.immutable or isinstance(instance, Immutable)
        convert, check = attr._convert_value, attr._check_value
        super().__init__((check(convert(value)) for value in values))

    # add(elem)
    add = _check_instance(_convert_n_check_value(set.add))
    # discard(elem)
    discard = _check_instance(_convert_n_check_value(set.discard))
    # clear()
    clear = _check_instance(set.clear)
    # pop()
    pop = _check_instance(set.pop)
    # remove(elem)
    remove = _check_instance(_convert_n_check_value(set.remove))
    # update(*others)
    update = _check_instance(_convert_n_check_value_sets(set.update))
    # self |= other | ...
    __ior__ = _check_instance(_convert_n_check_value_sets(set.__ior__))
    # intersection_update(*others)
    intersection_update = \
        _check_instance(_convert_n_check_value_sets(set.intersection_update))
    # self &= other & ...
    __iand__ = _check_instance(_convert_n_check_value_sets(set.__iand__))
    # difference_update(*others)
    difference_update = \
        _check_instance(_convert_n_check_value_sets(set.difference_update))
    # self -= other | ...
    __isub__ = _check_instance(_convert_n_check_value_sets(set.__isub__))
    # symmetric_difference_update(other)
    symmetric_difference_update = \
        _check_instance(_convert_n_check_value_sets(
                        set.symmetric_difference_update))
    # self ^= other
    __ixor__ = _check_instance(_convert_n_check_value_sets(set.__ixor__))

    def __repr__(self) -> str:
        """repr(self)"""
        return "<%r.%s: %s>" % (self._instance, self._attr.name, self)

    def __str__(self):
        """str(self)"""
        return str(set(self))


class MultiValueAttribute(Attribute):

    """Attribute that can hold multiple values (like a set)."""

    @property
    def default(self) -> Any:
        """Value or callable used to obtain a default value for the attribute.
        """
        return self._default

    @default.setter
    def default(self, default: Any) -> None:
        if default == _NODEFAULT or default is None:
            self._default = default
        elif callable(default):
            # wrap callable to provide a _MultiValue
            self._default = lambda instance: _MultiValue(self, None,
                                                         default(instance))
        else:
            # wrap default into a _MultiValue
            self._default = _MultiValue(self, None, default)

    def __set__(self, instance: object, values: Iterable) -> None:
        """Set values of managed multi-value attribute."""
        self._check_immutable(instance)
        setattr(instance, self._priv_member,
                _MultiValue(self, instance, values))


class _QualifiedMultiValue(dict):

    """Dict-like container for multiple values, linked to an instance and an
    attriute of that instance"""

    def __init__(self, attr: Attribute, instance: Any = None,
                 items: Union[Iterable, Mapping] = {}) -> None:
        self._attr = attr
        self._instance = instance
        self._immutable = attr.immutable or isinstance(instance, Immutable)
        check_key, convert, check_value = (attr._check_key,
                                           attr._convert_value,
                                           attr._check_value)
        try:    # a Mapping given?
            it = items.items()
        except AttributeError:
            it = items
        super().__init__(((check_key(key), check_value(convert(value)))
                          for (key, value) in it))

    # __setitem__(key, value, /)
    @_check_instance
    def __setitem__(self, key, value):
        attr = self._attr
        super().__setitem__(attr._check_key(key),
                            attr._check_value(attr._convert_value(value)))

    # __delitem__(key, /)
    __delitem__ = _check_instance(dict.__delitem__)
    # pop(key[, default])
    pop = _check_instance(dict.pop)
    # popitem()
    popitem = _check_instance(dict.popitem)
    # clear()
    clear = _check_instance(dict.clear)

    # update([other], **kwds)
    @_check_instance
    def update(self, other, **kwds):
        attr = self._attr
        check_key, convert, check_value = (attr._check_key,
                                           attr._convert_value,
                                           attr._check_value)
        try:    # a Mapping given?
            it = chain(other.items(), kwds.items())
        except AttributeError:
            it = chain(other, kwds.items())
        super().update(((check_key(key), check_value(convert(value)))
                        for (key, value) in it))

    # setdefault(key[, default])
    @_check_instance
    def setdefault(self, key, default=None):
        attr = self._attr
        return super().setdefault(attr._check_key(key),
                                  attr._check_value(
                                      attr._convert_value(default)))

    def __repr__(self) -> str:
        """repr(self)"""
        return "<%r.%s: %s>" % (self._instance, self._attr.name, self)

    def __str__(self):
        """str(self)"""
        return str(dict(self))


class QualifiedMultiValueAttribute(Attribute):

    """Attribute that can hold multiple values (like a dict)."""

    def __init__(self, key_type: type, immutable: bool = False,
                 default: Any = _NODEFAULT,
                 converter: Optional[ConverterType] = None,
                 constraints: ContraintsParamType = None,
                 doc: Optional[Text] = None) -> None:
        """Initialze multi-value attribute."""
        self._key_type = key_type
        super().__init__(immutable=immutable, default=default,
                         converter=converter, constraints=constraints,
                         doc=doc)

    def _check_key(self, key: Any) -> Any:
        if isinstance(key, self._key_type):
            return key
        raise TypeError("Given key '%s' is not an instance of '%s'" %
                        (key, self._key_type))

    @property
    def default(self) -> Any:
        """Value or callable used to obtain a default value for the attribute.
        """
        return self._default

    @default.setter
    def default(self, default: Any) -> None:
        if default == _NODEFAULT or default is None:
            self._default = default
        elif callable(default):
            # wrap callable to provide a _QualifiedMultiValue
            self._default = lambda instance: \
                _QualifiedMultiValue(self, None, default(instance))
        else:
            # wrap default into a _QualifiedMultiValue
            self._default = _QualifiedMultiValue(self, None, default)

    def __set__(self, instance: object, values: Union[Iterable, Mapping]) \
            -> None:
        """Set values of managed multi-value attribute."""
        self._check_immutable(instance)
        setattr(instance, self._priv_member,
                _QualifiedMultiValue(self, instance, values))


__all__ = [
    'AbstractAttribute',
    'Attribute',
    'MultiValueAttribute',
    'QualifiedMultiValueAttribute',
]
