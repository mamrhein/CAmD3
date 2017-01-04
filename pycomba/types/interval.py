# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Name:        interval
# Purpose:     Basic interval arithmetic
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


"""Basic interval arithmetic"""


#TODO: enhance doc

from collections import Container, Sequence, Mapping, Callable
from functools import total_ordering, partial
import operator

__metaclass__ = type

LOWER_LIMIT_SYMBOLS = ['(', '[']
UPPER_LIMIT_SYMBOLS = [')', ']']
INFINITY_SYMBOL = 'inf'
INTERVAL_SYMBOL = '..'
#???: should we use unicode symbols?
#INFINITY_SYMBOL = '∞'
#INTERVAL_SYMBOL = '…'


# --- Exceptions ---

class InvalidInterval(Exception):

    """Raised when an invalid Interval would be created."""


class EmptyIntervalChain(Exception):

    """Raised when an empty IntervalChain would be created."""


# --- Handling infinity ---

class _Inf:

    """Value representing infinity."""

    __slots__ = ()

    symbol = INFINITY_SYMBOL

    def __new__(cls):
        try:
            return cls._the_one_and_only
        except AttributeError:
            inf = object.__new__(cls)
            cls._the_one_and_only = inf
            return inf

    def __repr__(self):
        return "%s()" % self.__class__.__name__         # pragma: no cover

    def __str__(self):
        return self.symbol


@total_ordering
class Inf(_Inf):

    """Value representing (positive) infinity."""

    symbol = '+' + INFINITY_SYMBOL

    def __eq__(self, other):
        # singletons can savely be compared by identity
        return other is self

    # needed in Python 3.x:
    __hash__ = object.__hash__

    # there's nothing greater
    __le__ = __eq__


@total_ordering
class NegInf(_Inf):

    """Value representing negative infinity."""

    symbol = '-' + INFINITY_SYMBOL

    def __eq__(self, other):
        # singletons can savely be compared by identity
        return other is self

    # needed in Python 3.x:
    __hash__ = object.__hash__

    # there's nothing smaller
    __ge__ = __eq__


# --- Limits ---

class AbstractLimit:

    """Abstract base class of a Limit."""

    __slots__ = ()

    # used to map (is_lower, is_closed) to operator in method is_observed_by
    _ops = ((operator.lt, operator.le), (operator.gt, operator.ge))

    def __init__(self):
        raise NotImplementedError

    def is_lower(self):
        """True if self is lower endpoint, False otherwise."""
        return self._lower

    def is_upper(self):
        """True if self is upper endpoint, False otherwise."""
        return not self.is_lower()

    @property
    def value(self):
        """The limiting value."""
        return self._value

    def is_observed_by(self, value):
        """True if value does not exceed the limit."""
        op = self._ops[self.is_lower()][self.is_closed()]
        return op(value, self.value)

    def is_closed(self):
        """True if self is closed endpoint, False otherwise."""
        return self._closed

    def is_open(self):
        """True if self is open endpoint, False otherwise."""
        return not self.is_closed()

    def is_lower_adjacent(self, other):
        """True if self < other and Interval(self, other) is empty."""
        return self < other and self.value == other.value

    def is_upper_adjacent(self, other):
        """True if self > other and Interval(other, self) is empty."""
        return self > other and self.value == other.value

    def is_adjacent(self, other):
        """True if self.is_lower_adjacent(other) or
        self.is_upper_adjacent(other)."""
        return self.is_lower_adjacent(other) or self.is_upper_adjacent(other)

    def adjacent_limit(self):
        """Return the limit adjacent to self."""
        raise NotImplementedError

    def __copy__(self):
        """Return self (Limit instances are immutable)."""
        return self

    def __deepcopy__(self, memo):
        return self.__copy__()

    def __str__(self):
        value = self.value
        if isinstance(value, (bytes, str)):
            value = "'%s'" % value
        if self.is_lower():
            return "%s%s" % (LOWER_LIMIT_SYMBOLS[self.is_closed()], value)
        else:
            return "%s%s" % (value, UPPER_LIMIT_SYMBOLS[self.is_closed()])


@total_ordering
class InfiniteLimit(AbstractLimit):

    """Lower / upper limit of an unbounded (aka infinite) Interval."""

    __slots__ = ['_lower']

    # dict holding singletons for lower and upper infinite limit
    _singletons = {}

    def __new__(cls, lower):
        """Initialize InfiniteLimit instance.

        lower       specifies which endpoint of an interval this limit defines
                    (must be of type bool):
                    True:   lower endpoint
                    False:  upper endpoint
        """
        assert isinstance(lower, bool)
        try:
            return cls._singletons[lower]
        except KeyError:
            inf = super(InfiniteLimit, cls).__new__(cls)
            cls._singletons[lower] = inf
            return inf

    def __init__(self, lower):
        """Initialize InfiniteLimit instance.

        lower       specifies which endpoint of an interval this limit defines
                    (must be of type bool):
                    True:   lower endpoint
                    False:  upper endpoint
        """
        self._lower = lower

    @property
    def value(self):
        """Lower / upper infinity."""
        if self.is_lower():
            return NegInf()
        else:
            return Inf()

    def is_closed(self):
        """False (infinite endpoints is always open)."""
        return False

    def adjacent_limit(self):
        """Return None because an infinite limit has no adjacent limit."""
        return None

    def __hash__(self):
        """hash(self)"""
        return hash((self.is_lower(), self.value, False))

    def __eq__(self, other):
        """self == other"""
        # singletons can savely be compared by identity
        return other is self

    def __lt__(self, other):
        """self < other"""
        # self is lower limit => self.value == NegInf and
        # self is upper limit => self.value == Inf,
        # so we can savely delegate comparison to the values
        try:
            return self.value < other.value
        except AttributeError:
            # other is not a Limit, so take it as value
            return self.value < other

    def __repr__(self):                                 # pragma: no cover
        return "%sInfiniteLimit()" % ['Upper', 'Lower'][self.is_lower()]

# Two factory functions for creating the infinite limits

LowerInfiniteLimit = partial(InfiniteLimit, True)
UpperInfiniteLimit = partial(InfiniteLimit, False)


class Limit(AbstractLimit):

    """Lower / upper limit of an Interval."""

    __slots__ = ['_lower', '_value', '_closed']

    def __init__(self, lower, value, closed=True):
        """Initialize Limit instance.

        lower       specifies which endpoint of an interval this limit defines
                    (must be of type bool):
                    True:   lower endpoint
                    False:  upper endpoint
        value       limiting value (can be of any type that defines an
                    ordering)
        closed      specifies whether value itself is the endpoint or not
                    (must be of type bool):
                    True:   the interval that has this limit includes value
                    False:  the interval that has this limit does not
                            includes value
        """
        assert isinstance(lower, bool)
        # prevent undefined limit
        assert value is not None
        # for infinite limit use InfiniteLimit
        assert not isinstance(value, _Inf)
        #???: Check whether type of value defines an ordering?
        assert isinstance(closed, bool)
        self._lower = lower
        self._value = value
        self._closed = closed

    def _map_limit_type(self):
        # upper+open < closed < lower+open
        if self.is_closed():
            return 0
        if self.is_lower():
            return 1
        return -1

    def _compare(self, other, op):
        if isinstance(other, Limit):
            self_val, other_val = self.value, other.value
            if self_val == other_val:
                # if limit values are equal, result depends on limit types
                return op(self._map_limit_type(), other._map_limit_type())
            return op(self_val, other_val)
        else:
            self_val = self.value
            try:
                # is other comparable to self.value?
                if self_val == other:
                    # if values are equal, result depends on limit type
                    return op(self._map_limit_type(), 0)
                return op(self_val, other)
            except TypeError:                           # pragma: no cover
                return NotImplemented

    def adjacent_limit(self):
        """Return the limit adjacent to self."""
        return Limit(not self.is_lower(), self.value, not self.is_closed())

    def __hash__(self):
        """hash(self)"""
        return hash((self.is_lower(), self.value, self.is_closed()))

    def __eq__(self, other):
        """self == other"""
        return self._compare(other, operator.eq)

    def __lt__(self, other):
        """self < other"""
        return self._compare(other, operator.lt)

    def __le__(self, other):
        """self <= other"""
        return self._compare(other, operator.le)

    def __gt__(self, other):
        """self > other"""
        return self._compare(other, operator.gt)

    def __ge__(self, other):
        """self >= other"""
        return self._compare(other, operator.ge)

    def __repr__(self):                                 # pragma: no cover
        return "%s(%s, %s, %s)" % (self.__class__.__name__,
                                   self.is_lower(),
                                   repr(self.value),
                                   self.is_closed())

# Some factory functions for creating limits

LowerLimit = partial(Limit, True)
UpperLimit = partial(Limit, False)

LowerClosedLimit = partial(Limit, True, closed=True)
LowerOpenLimit = partial(Limit, True, closed=False)
UpperClosedLimit = partial(Limit, False, closed=True)
UpperOpenLimit = partial(Limit, False, closed=False)


# --- Intervals ---

class Interval(Container):

    """An Interval defines a subset of a set of values by optionally giving
    a lower and / or an upper limit.

    The base set of values - and therefore the given limits - must have a
    common base type which defines a total order on the values.

    If both limits are given, the interval is said to be *bounded* or
    *finite*, if only one or neither of them is given, the interval is said
    to be *unbounded* or *infinite*.

    If only the lower limit is given, the interval is called *lower bounded*
    or *left bounded* (maybe also *upper unbounded*, *upper infinite*,
    *right unbounded* or *right infinite*). Correspondingly, if only the
    upper limit is given, the interval is called *upper bounded*
    or *right bounded* (maybe also *lower unbounded*, *lower infinite*,
    *left unbounded* or *left infinite*).

    For both limits (aka endpoints) must be specified whether the given value
    is included in the interval or not. In the first case the limit is called
    *closed*, otherwise *open*.
    """

    def __init__(self, lower_limit=None, upper_limit=None):
        """Initialize Interval instance.

        Raises InvalidInterval exception when
        * lower limit is not a lower limit, or
        * upper limit is not an upper limit, or
        * lower_limit > upper_limit.
        """
        if lower_limit is not None and lower_limit != LowerInfiniteLimit():
            if lower_limit.is_upper():
                raise InvalidInterval("Given lower limit is an upper limit.")
            self._lower_limit = lower_limit
        if upper_limit is not None and upper_limit != UpperInfiniteLimit():
            if upper_limit.is_lower():
                raise InvalidInterval("Given upper limit is a lower limit.")
            self._upper_limit = upper_limit
        if self.lower_limit > self.upper_limit:
            raise InvalidInterval("Given lower limit > given upper limit.")

    @property
    def lower_limit(self):
        """Lower limit (LowerInfiniteLimit, if no lower limit was given.)"""
        try:
            return self._lower_limit
        except AttributeError:
            return LowerInfiniteLimit()

    @property
    def upper_limit(self):
        """Upper limit (UpperInfiniteLimit, if no upper limit was given.)"""
        try:
            return self._upper_limit
        except AttributeError:
            return UpperInfiniteLimit()

    @property
    def _limits(self):
        limits = []
        try:
            limits.append(self._lower_limit)
        except AttributeError:
            pass
        try:
            limits.append(self._upper_limit)
        except AttributeError:
            pass
        return limits

    @property
    def limits(self):
        """Lower and upper limit as tuple."""
        return (self.lower_limit, self.upper_limit)

    def is_lower_bounded(self):
        try:
            return self._lower_limit and True
        except AttributeError:
            return False
    # alternate name
    is_left_bounded = is_lower_bounded

    def is_upper_bounded(self):
        try:
            return self._upper_limit and True
        except AttributeError:
            return False
    # alternate name
    is_right_bounded = is_upper_bounded

    def is_bounded(self):
        return self.is_lower_bounded() and self.is_upper_bounded()
    # alternate name
    is_finite = is_bounded

    def is_lower_unbounded(self):
        return not self.is_lower_bounded()

    def is_upper_unbounded(self):
        return not self.is_upper_bounded()

    def is_unbounded(self):
        return self.is_lower_unbounded() or self.is_upper_unbounded()
    # alternate name
    is_infinite = is_unbounded

    def is_lower_closed(self):
        return self.lower_limit.is_closed()
    # alternate name
    is_left_closed = is_lower_closed

    def is_upper_closed(self):
        return self.upper_limit.is_closed()
    # alternate name
    is_right_closed = is_upper_closed

    def is_closed(self):
        return self.is_lower_closed() and self.is_upper_closed()

    def is_lower_open(self):
        return self.lower_limit.is_open()
    # alternate name
    is_left_open = is_lower_open

    def is_upper_open(self):
        return self.upper_limit.is_open()
    # alternate name
    is_right_open = is_upper_open

    def is_open(self):
        return self.is_lower_open() or self.is_upper_open()

    def __contains__(self, value):
        """True if value does not exceed the limits of self."""
        return all((limit.is_observed_by(value) for limit in self._limits))

    def __eq__(self, other):
        """self == other.

        True if all elements contained in self are also contained in other
        and all elements contained in other are also contained in self.

        This is exactly the case if self.limits == other.limits."""
        if isinstance(other, Interval):
            return self.limits == other.limits
        return NotImplemented

    def __lt__(self, other):
        """self < other.

        True if there is an element in self which is smaller than all
        elements in other or there is an element in other which is greater
        than all elements in self.

        This is exactly the case if self.limits < other.limits."""
        if isinstance(other, Interval):
            return self.limits < other.limits
        return NotImplemented

    def __le__(self, other):
        """self <= other."""
        if isinstance(other, Interval):
            return self.limits <= other.limits
        return NotImplemented

    def __gt__(self, other):
        """self > other.

        True if there is an element in self which is greater than all
        elements in other or there is an element in other which is smaller
        than all elements in self.

        This is exactly the case if self.limits > other.limits."""
        if isinstance(other, Interval):
            return self.limits > other.limits
        return NotImplemented

    def __ge__(self, other):
        """self >= other."""
        if isinstance(other, Interval):
            return self.limits >= other.limits
        return NotImplemented

    def is_subset(self, other):
        """True if self defines a proper subset of other, i.e. all elements
        contained in self are also contained in other, but not the other way
        round."""
        return (self.lower_limit >= other.lower_limit and
                self.upper_limit <= other.upper_limit and
                self != other)

    def is_disjoint(self, other):
        """"True if self contains no elements in common with other."""
        return (self.lower_limit > other.upper_limit or
                self.upper_limit < other.lower_limit)

    def is_overlapping(self, other):
        """"True if there is a common element in self and other."""
        return not self.is_disjoint(other)

    def is_lower_adjacent(self, other):
        """True if self.upper_limit.is_lower_adjacent(other.lower_limit)."""
        return self.upper_limit.is_lower_adjacent(other.lower_limit)

    def is_upper_adjacent(self, other):
        """True if self.lower_limit.is_upper_adjacent(other.upper_limit)."""
        return self.lower_limit.is_upper_adjacent(other.upper_limit)

    def is_adjacent(self, other):
        """True if self.is_lower_adjacent(other) or
        self.is_upper_adjacent(other)."""
        return self.is_lower_adjacent(other) or self.is_upper_adjacent(other)

    def __and__(self, other):
        """self & other"""
        if isinstance(other, Interval):
            if self.is_disjoint(other):
                raise InvalidInterval("Intervals are disjoint, " +
                                      "so intersection is not an Interval.")
            lower_limit = max(self.lower_limit, other.lower_limit)
            upper_limit = min(self.upper_limit, other.upper_limit)
            return Interval(lower_limit, upper_limit)
        return NotImplemented

    def __or__(self, other):
        """self | other"""
        if isinstance(other, Interval):
            if self.is_overlapping(other) or self.is_adjacent(other):
                lower_limit = min(self.lower_limit, other.lower_limit)
                upper_limit = max(self.upper_limit, other.upper_limit)
                return Interval(lower_limit, upper_limit)
            raise InvalidInterval("Intervals are disjoint and not adjacent, "
                                  "so union is not an Interval")
        return NotImplemented

    def __sub__(self, other):
        """self - other"""
        if isinstance(other, Interval):
            if self.lower_limit >= other.lower_limit:
                if self.upper_limit <= other.upper_limit:
                    raise InvalidInterval("self is subset of other, "
                                          "so result is not an Interval.")
                else:
                    lower_limit = max(self.lower_limit,
                                      other.upper_limit.adjacent_limit())
                    upper_limit = self.upper_limit
            else:
                if self.upper_limit <= other.upper_limit:
                    lower_limit = self.lower_limit
                    upper_limit = min(self.upper_limit,
                                      other.lower_limit.adjacent_limit())
                else:
                    raise InvalidInterval("other is subset of self, "
                                          "so result is not an Interval.")
            return Interval(lower_limit, upper_limit)
        return NotImplemented

    def __hash__(self):
        """hash(self)"""
        return hash(self.limits)

    def __copy__(self):
        """Return self (Interval instances are immutable)."""
        return self

    def __deepcopy__(self, memo):
        return self.__copy__()

    def __repr__(self):
        params = ["%s_limit=%r" % (['upper', 'lower'][l.is_lower()], l)
                  for l in self._limits]
        return "%s(%s)" % (self.__class__.__name__, ', '.join(params))

    def __str__(self):
        return "%s %s %s" % (self.lower_limit,
                             INTERVAL_SYMBOL,
                             self.upper_limit)


# Some factory functions for creating intervals

def ClosedInterval(lower_value, upper_value):
    """Create Interval with closed endpoints."""
    return Interval(lower_limit=LowerClosedLimit(lower_value),
                    upper_limit=UpperClosedLimit(upper_value))


def OpenBoundedInterval(lower_value, upper_value):
    """Create Interval with open endpoints."""
    return Interval(lower_limit=LowerOpenLimit(lower_value),
                    upper_limit=UpperOpenLimit(upper_value))
# alternate name
OpenFiniteInterval = OpenBoundedInterval


def LowerClosedInterval(lower_value):
    """Create Interval with closed lower and infinite upper endpoint."""
    return Interval(lower_limit=LowerClosedLimit(lower_value))


def UpperClosedInterval(upper_value):
    """Create Interval with infinite lower and closed upper endpoint."""
    return Interval(upper_limit=UpperClosedLimit(upper_value))


def LowerOpenInterval(lower_value):
    """Create Interval with open lower and infinite upper endpoint."""
    return Interval(lower_limit=LowerOpenLimit(lower_value))


def UpperOpenInterval(upper_value):
    """Create Interval with infinite lower and open upper endpoint."""
    return Interval(upper_limit=UpperOpenLimit(upper_value))


def ChainableInterval(lower_value, upper_value, lower_closed=True):
    """Create Interval with one closed and one open endpoint."""
    if lower_closed:
        return Interval(lower_limit=LowerClosedLimit(lower_value),
                        upper_limit=UpperOpenLimit(upper_value))
    else:
        return Interval(lower_limit=LowerOpenLimit(lower_value),
                        upper_limit=UpperClosedLimit(upper_value))


# --- Interval chain ---

class IntervalChain(Sequence):

    """An IntervalChain is a list of adjacent intervals.

    It is constructed from a list of limiting values."""

    def __init__(self, limits, lower_closed=True, add_lower_inf=False,
                 add_upper_inf=True):
        """Initialize instance of IntervalChain.

        limits              an iterable of the limiting values, must be
                            ordered from smallest to greatest
        lower_closed        boolean that defined which endpoint of the
                            contained intervals will be closed:
                            True:   lower endpoint closed, upper open
                                    (default)
                            False:  lower endpoint open, upper closed
        add_lower_inf       boolean that defines whether a lower infinite
                            interval will be added as first interval
                            True:   infinite interval as lowest interval
                            False:  no infinite interval as lowest interval
                                    (default)
        add_upper_inf       boolean that defines whether an upper infinite
                            interval will be added as last interval
                            True:   infinite interval as last interval
                                    (default)
                            False:  no infinite interval as last interval
        """
        n = len(limits)
        if n == 0 or (n == 1 and not add_lower_inf and not add_upper_inf):
            raise EmptyIntervalChain(
                "Given limits do not define any interval.")
        # the iterable 'limits' needs to be copied
        self._limits = tuple(limits)
        self._lower_closed = lower_closed
        ivals = []
        if add_lower_inf:
            # add lower infinite interval
            if lower_closed:
                ivals.append(UpperOpenInterval(limits[0]))
            else:
                ivals.append(UpperClosedInterval(limits[0]))
            self._lower_inf = True
        else:
            self._lower_inf = False
        # create chainable interval from values in limits
        try:
            ivals.extend([ChainableInterval(lower_value, upper_value,
                                            lower_closed=lower_closed)
                          for (lower_value, upper_value)
                          in zip(limits[:-1], limits[1:])])
        except InvalidInterval:
            raise InvalidInterval("Limits must be given in ascending order.")
        if add_upper_inf:
            # add upper infinite interval
            if lower_closed:
                ivals.append(LowerClosedInterval(limits[-1]))
            else:
                ivals.append(LowerOpenInterval(limits[-1]))
            self._upper_inf = True
        else:
            self._upper_inf = False
        self._ivals = ivals

    @property
    def limits(self):
        """The limiting values."""
        return self._limits

    @property
    def total_interval(self):
        """Returns the interval between lower endpoint of first interval in
        self and upper endpoint of last interval in self."""
        return Interval(self[0].lower_limit, self[-1].upper_limit)

    def is_lower_infinite(self):
        """True if first interval is lower infinite."""
        return self._lower_inf

    def is_upper_infinite(self):
        """True if last interval is upper infinite."""
        return self._upper_inf

    def map2idx(self, value):
        #TODO: find better name
        """Return the index of the interval which contains value.

        Raises ValueError if value is not contained in any of the intervals in
        self."""
        n = len(self)
        # using binary search
        left, right = (0, n - 1)
        while left <= right:
            idx = (right + left) // 2
            ival = self[idx]
            if value in ival:
                return idx
            if value < ival.lower_limit:
                right = idx - 1
            else:
                left = idx + 1
        raise ValueError("%r not in any interval of %r." % (value, self))

    def __copy__(self):
        """Return self (IntervalChain instances are immutable)."""
        return self

    def __eq__(self, other):
        """self == other"""
        if isinstance(other, IntervalChain):
            # interval chains are equal if their intervals are equal
            return self is other or self._ivals == other._ivals
        return NotImplemented

    def __getitem__(self, idx):
        """self[idx]"""
        return self._ivals[idx]

    def __iter__(self):
        """iter(self)"""
        return iter(self._ivals)

    def __len__(self):
        """len(self)"""
        return len(self._ivals)

    def __repr__(self):
        """repr(self)"""
        kwds = '' if self._lower_closed else ", lower_closed=False"
        if self.is_lower_infinite():
            kwds += ", add_lower_inf=True"
        if not self.is_upper_infinite():
            kwds += ", add_upper_inf=False"
        return "%s(%s%s)" % (self.__class__.__name__, self.limits, kwds)

    def __str__(self):
        """str(self)"""
        return '[%s]' % ', '.join([str(i) for i in self])


# --- Interval mapping ---

class IntervalMapping(Mapping, Callable):

    """An IntervalMapping is a container of associated interval / value pairs.

    It is constructed from either
      * an IntervalChain and a sequence of associated values,
      * a sequence of limiting values and a sequence of associated values,
      * a sequence of tuples, each holding a limiting value and an associated
        value.
    """

    def __init__(self, *args):
        """Initialize instance of IntervalMapping.
        """
        nargs = len(args)
        if nargs == 2:
            keys, vals = args
            assert len(keys) == len(vals), \
                "The given sequences must be of equal length."
            if not isinstance(keys, IntervalChain):
                assert len(keys) > 0, \
                    "The given sequences must not be empty."
                keys = IntervalChain(keys)
        elif nargs == 1:
            try:
                limits = [t[0] for t in args[0]]
                vals = [t[1] for t in args[0]]
            except (TypeError, IndexError):
                raise TypeError("Expected a sequence of 2-tuples.")
            keys = IntervalChain(limits)
        else:
            raise TypeError("1 or 2 arguments expected, got %s." % nargs)
        # interval chains are immutable, so no need to store a copy here, ...
        self._keys = keys
        # ... but the value sequence has to be copied
        self._vals = tuple(vals)

    def map(self, val):
        """self.map(val) -> result, i.e. the value associated with interval
        which contains val.
        """
        try:
            idx = self._keys.map2idx(val)
        except ValueError:
            raise KeyError("%s not in %s."
                           % (val, self._keys.total_interval))
        else:
            return self._vals[idx]

    def __call__(self, val):
        """self(val) -> result, i.e. the value associated with interval
        which contains val.
        """
        return self.map(val)

    def __copy__(self):
        """Return self (IntervalMapping instances are immutable)."""
        return self

    def __eq__(self, other):
        """self == other"""
        if isinstance(other, IntervalMapping):
            # interval mappings are equal if their intervals and values are
            # equal
            return self is other or (self._keys == other._keys and
                                     self._vals == other._vals)
        return NotImplemented

    def __getitem__(self, key):
        """self[key]"""
        try:
            idx = self._keys.index(key)
        except ValueError:
            raise KeyError("%s not in %s." % (key, self._keys))
        else:
            return self._vals[idx]

    def __iter__(self):
        """iter(self)"""
        return iter(self._keys)

    def __len__(self):
        """len(self)"""
        return len(self._keys)
