# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        siganature
# Purpose:     Get type signature of callables from annotations
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


"""Get type signature of callables from annotations"""


import importlib
import inspect
from typing import (
    Any, Callable, Optional, Sequence, Text, Tuple, TypingMeta, _TypingBase,
    Union
)

NoneType = type(None)

#_POSITIONAL_ONLY = inspect.Parameter.POSITIONAL_ONLY
#_POSITIONAL_OR_KEYWORD = inspect.Parameter.POSITIONAL_OR_KEYWORD
_VAR_POSITIONAL = inspect.Parameter.VAR_POSITIONAL
_KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY
_VAR_KEYWORD = inspect.Parameter.VAR_KEYWORD

# types of built-in functions and method wrappers
EXCL_FUNC_TYPES = (type(object.__init__),   # wrapper_descriptor
                   type(all),               # builtin_function_or_method
                   type(all.__call__),      # method-wrapper
                   )


def _get_constructor(cls):
    for func in (cls.__init__, cls.__new__, type(cls).__call__):
        if type(func) not in EXCL_FUNC_TYPES:
            return func
    return None


def _type_repr(t: type, prefix: str = '<', suffix: str = '>') -> str:
    if isinstance(t, (TypingMeta, _TypingBase)):
        if t.__origin__ is Union and t.__args__[-1] is NoneType:
            # special case Optional
            s = "Optional[{}]".format(_type_repr(t.__args__[0],
                                                 prefix='', suffix=''))
        else:
            # strip module name
            s = repr(t).replace('typing.', '')
    else:
        s = t.__name__
    return ''.join((prefix, s, suffix))


def _is_instance(obj, cls):
    try:
        return isinstance(obj, cls)
    except TypeError:
        # handle special cases not handled in typing.py
        # treat any object as instance of Any
        if cls is Any:
            return True
        # treat a tuple as instance of a parameterized tuple T if each of its
        # members is an instance of the corresponding parameter of T
        if issubclass(cls, Tuple):
            if isinstance(obj, Tuple):
                cls_args = cls.__args__
                if cls_args[-1] == Ellipsis:
                    item_cls = cls_args[0]
                    if all(_is_instance(item, item_cls)
                           for item in obj):
                        return True
                    return False
                if len(cls_args) != len(obj):
                    return False
                if all(_is_instance(item, cls_arg)
                       for item, cls_arg
                       in zip(obj, cls_args)):
                    return True
            return False


def _is_subclass(subcls, cls):
    try:
        return issubclass(subcls, cls)
    except TypeError:
        # handle special cases not handled in typing.py
        # treat every class as its own subclass
        if subcls is cls:
            return True
        # treat any class as subclass of Any
        if cls is Any:
            return True
        # treat a parameterized Tuple T1 as a subclass of a parameterized
        # Tuple T2, if they have the same number of parameters and
        # if each parameter of T1 is a subclass of the corresponding parameter
        # of T2
        if issubclass(cls, Tuple):
            if issubclass(subcls, Tuple):
                try:
                    cls_args = cls.__args__
                    subcls_args = subcls.__args__
                except AttributeError:
                    return False
                if len(cls_args) != len(subcls_args):
                    return False
                if cls_args[-1] == Ellipsis:
                    if subcls_args[-1] == Ellipsis:
                        if _is_subclass(subcls_args[0], cls_args[0]):
                            return True
                    return False
                if all(_is_subclass(subcls_arg, cls_arg)
                       for subcls_arg, cls_arg
                       in zip(subcls_args, cls_args)):
                    return True
            return False


def _is_compatible(t1, t2):
    # a subclass is compatible
    try:
        if _is_subclass(t1, t2):
            return True
    except TypeError:
        pass
    # None ?
    if t1 is None and t2 is None:
        return True
    # if t1 is None or t2 is None:
    #     return False
    return False


class Signature:

    """A Signature object represents the types of the parameters and the
    return value of a callable.

    Args:

    Returns:

    Raises:
    """

    __slots__ = ('_arg_types', '_var_arg_type', '_return_type')

    def __init__(self, arg_types: Sequence[type],
                 var_arg_type: Optional[type] = None,
                 return_type: Optional[type] = None) -> None:
        """Initialize Signature object."""
        self._arg_types = tuple(arg_types)
        self._var_arg_type = var_arg_type
        self._return_type = return_type

    @classmethod
    def from_callable(cls, obj: Callable) -> 'Signature':
        """Create a signature of the callable `obj`.

        Args:
            obj(Callable): callable to be analyzed

        Returns:
            Signature: :class:`Signature` instance holding the types of the
                non-default arguments and the type of the return value of
                `obj`

        Raises:
            AssertionError: `obj` is not callable
            ValueError: `obj` has keyword-only arg(s) w/o default value
            ValueError: `obj` has arg(s) w/o type hint
            ValueError: signature of `obj` couldn't be retrieved
        """
        namespace = None
        arg_types = []
        var_arg_type = None
        if isinstance(obj, type):               # it's a class?
            try:
                sig = inspect.signature(_get_constructor(obj) or obj)
            except (TypeError, ValueError):
                sig = None
            skip_arg = 1
        else:
            try:
                sig = inspect.signature(obj)
            except TypeError:
                sig = None
            skip_arg = 0
        if sig:
            return_type = sig.return_annotation
            if return_type is sig.empty:
                if isinstance(obj, type):
                    return_type = obj
                else:
                    return_type = Any
            elif return_type is None and isinstance(obj, type):
                return_type = obj
            elif isinstance(return_type, Text):
                namespace = (namespace or
                             importlib.import_module(obj.__module__).__dict__)
                return_type = eval(return_type, namespace)
            non_def_args = [(p.name, p.kind, p.annotation)
                            for p in list(sig.parameters.values())[skip_arg:]
                            if p.default is sig.empty]
            for name, kind, annotation in non_def_args:
                if kind in (_KEYWORD_ONLY, _VAR_KEYWORD):
                    raise ValueError("'" + repr(obj) + "' has keyword-only "
                                     "arg w/o default value: '" + name + "'.")
                if annotation is sig.empty:
                    raise ValueError("'" + repr(obj) + "' has arg"
                                     " w/o type hint: '" + name + "'.")
                if isinstance(annotation, Text):
                    namespace = (namespace or
                                 importlib.import_module(obj.__module__)
                                 .__dict__)
                    try:
                        annotation = eval(annotation, namespace)
                    except NameError:
                        annotation = None
                if isinstance(annotation, type):
                    if kind == _VAR_POSITIONAL:
                        var_arg_type = annotation
                    else:
                        arg_types.append(annotation)
                else:
                    raise ValueError("'" + repr(obj) + "' has arg"
                                     " w/o type hint: '" + name + "'.")
            if arg_types or var_arg_type or return_type:
                return cls(arg_types, var_arg_type=var_arg_type,
                           return_type=return_type)
        raise ValueError("Can't retrieve signature of '" + repr(obj) + "'.")

    @property
    def arg_types(self) -> Tuple[type, ...]:
        return self._arg_types

    @property
    def var_arg_type(self) -> Optional[type]:
        return self._var_arg_type

    @property
    def return_type(self) -> Optional[type]:
        return self._return_type

    def is_compatible_to(self, other: 'Signature') -> bool:
        """Return True if `self` is compatible to `other`."""
        if self is other or self == other:
            return True
        # self.return_type must be compatible to other.return_type
        self_return_type, other_return_type = (self.return_type,
                                               other.return_type)
        # if self_return_type is None and other_return_type is not None:
        #     return False
        # if self_return_type is not None and other_return_type is None:
        #     return False
        if not _is_compatible(self_return_type, other_return_type):
            return False
        # other.var_arg_type must be compatible to self.var_arg_type
        self_var_arg_type, other_var_arg_type = (self.var_arg_type,
                                                 other.var_arg_type)
        # if self_var_arg_type is None and other_var_arg_type is not None:
        #     return False
        # if self_var_arg_type is not None and other_var_arg_type is None:
        #     return False
        if not _is_compatible(other_var_arg_type, self_var_arg_type):
            return False
        # each type in other.arg_types must compatible the corresponding
        # type on self.arg_types
        self_arg_types, other_arg_types = self.arg_types, other.arg_types
        if len(self_arg_types) != len(other_arg_types):
            return False
        return (all((_is_compatible(oat, sat)
                     for (oat, sat) in zip(other_arg_types, self_arg_types))))

    def __getstate__(self) \
            -> Tuple[Tuple[type, ...], Optional[type], Optional[type]]:
        return (self.arg_types, self.var_arg_type, self.return_type)

    def __eq__(self, other: object) -> bool:
        """self == other"""
        return (isinstance(other, Signature) and
                self.__getstate__() == other.__getstate__())

    def __hash__(self) -> int:
        """hash(self)"""
        return hash(self.__getstate__())

    def __str__(self) -> str:
        """str(self)"""
        args = ', '.join((_type_repr(t) for t in self.arg_types))
        var_arg_type = self.var_arg_type
        if var_arg_type is not None:
            if args:
                args += ', *' + _type_repr(var_arg_type)
            else:
                args = '*' + _type_repr(var_arg_type)
        return_type = self.return_type
        if return_type is None:
            return "({}) -> None".format(args)
        return "({}) -> {}".format(args, _type_repr(return_type))

    def __repr__(self) -> str:
        """repr(self)"""
        return "<{} {}>".format(self.__class__.__name__, str(self))


def signature(obj: Callable) -> Signature:
    """Retrieve the type signature of the callable `obj`.

    Args:
        obj(Callable): callable to be analyzed

    Returns:
        Signature: :class:`Signature` instance holding the types of the
            non-default arguments and the type of the return value of `obj`

    Raises:
        AssertionError: `obj` is not callable
        ValueError: `obj` has keyword-only arg(s) w/o default value
        ValueError: `obj` has arg(s) w/o type hint
        ValueError: signature of `obj` couldn't be retrieved
    """
    return Signature.from_callable(obj)


__all__ = [
    'Signature',
    'signature',
]
