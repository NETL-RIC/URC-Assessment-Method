"""Logic for handling no data values during various steps of the simulation."""


class NoDataSentinel(object):
    """Value used to represent No Data in equations.

    The sentinel will return different values when used in arithmetic operations, depending on its attributes:

      * If ``ignore`` is `True`, the sentinel will return the other operand in binary operations.
      * If ``ignore`` is `False` and ``subVal`` is `None`, the sentinel will return itself.
      * If ``ignore`` is `False` and ``subVal`` is not `None`, ``subVal`` is used in the binary operation
        and the result is returned.

    Attributes:
        ignore (bool): Flag indicating if the sentinel should be ignored in arithmetic operations.
        subVal (float): Only referenced if ``ignore`` is `False`. The value to substitute in place of the
          sentinel value, if any.

    Args:
            ignore (bool,optional): The default state of the ignore attribute. Defaults to `True`.
            subVal (float,optional): The default value for the subVal attribute. Defaults to `None`.

    """

    def __init__(self, ignore=True, subval=None):

        self.ignore = ignore
        self.subVal = subval

    def _do_unaryop(self, opfunc):
        """Generic handler for unary operations.

        Args:
            opfunc (function): The unary function to carry out if configured to use a substitution value.

        Returns:
            NoDataSentinel: If ``self.ignore`` is set to `True`. This is self.
            NoDataSentinel: If ``self.ignore`` is set to `False` and ``self.subVal`` is `None`. This is self.
            float: If ``self.ignore`` is set to `False` and ``self.subVal`` is not `None`. This is the result of
              ``opFunc``

        """

        if self.ignore:
            return self  # None
        if self.subVal is None:
            return self

        return opfunc(self.subVal)

    def _do_binaryop(self, other, opfunc):
        """Generic handler for binary operations.

        Args:
            other (float): The other operand in the operation.
            opfunc (function): The binary function to carry out if configured to use a substitution value.

        Returns:
            float: If ``self.ignore`` is set to `True`. This is the other operand's value.
            NoDataSentinel: If ``self.ignore`` is set to `False` and ``self.subVal`` is `None`. This is self.
            float: If ``self.ignore`` is set to `False` and ``self.subVal`` is not `None`. This is the result of
              ``opFunc``

        """
        if self.ignore:
            return other
        if self.subVal is None:
            return self
        return opfunc(self.subVal, other)

    def __repr__(self):
        ret = '"No Data Sentinel" '

        if self.ignore:
            ret += 'set to be ignored.'
        elif self.subVal is None:
            ret += 'to be passed through.'
        else:
            ret += 'with substitution of ' + str(self.subVal)
        return ret

    def __str__(self):

        if self.ignore:
            return 'None'
        elif self.subVal is None:
            return 'NoVal sentinel'

        return str(self.subVal)

    def __float__(self):

        if self.ignore or self.subVal is None:
            return None

        return self.subVal

    # def __lt__(self, other):
    #     return self._doBiCompare(other, lambda s, o: s < o)
    #
    # def __le__(self, other):
    #     return self._doBiCompare(other, lambda s, o: s <= o)
    #
    # def __eq__(self, other):
    #     return self._doBiCompare(other, lambda s, o: s == o)
    #
    # def __ne__(self, other):
    #     return self._doBiCompare(other, lambda s, o: s != o)
    #
    # def __gt__(self, other):
    #     return self._doBiCompare(other, lambda s, o: s > o)
    #
    # def __ge__(self, other):
    #     return self._doBiCompare(other, lambda s, o: s >= o)

    def __add__(self, other):
        return self._do_binaryop(other, lambda s, o: s + o)

    def __sub__(self, other):
        return self._do_binaryop(other, lambda s, o: s - o)

    def __mul__(self, other):
        return self._do_binaryop(other, lambda s, o: s * o)

    def __truediv__(self, other):
        return self._do_binaryop(other, lambda s, o: s / o)

    def __floordiv__(self, other):
        return self._do_binaryop(other, lambda s, o: s // o)

    def __mod__(self, other):
        return self._do_binaryop(other, lambda s, o: s % o)

    def __divmod__(self, other):
        return self._do_binaryop(other, lambda s, o: (s // o, s % o))

    def __pow__(self, other, modulo=None):
        return self._do_binaryop(other, lambda s, o: pow(s, o, modulo))

    def __radd__(self, other):
        return self._do_binaryop(other, lambda s, o: o + s)

    def __rsub__(self, other):
        return self._do_binaryop(other, lambda s, o: o - s)

    def __rmul__(self, other):
        return self._do_binaryop(other, lambda s, o: o * s)

    def __rdiv__(self, other):
        return self._do_binaryop(other, lambda s, o: o / s)

    def __rfloordiv__(self, other):
        return self._do_binaryop(other, lambda s, o: o // s)

    def __rmod__(self, other):
        return self._do_binaryop(other, lambda s, o: o % s)

    def __rdivmod__(self, other):
        return self._do_binaryop(other, lambda s, o: (o // s, o % s))

    def __rpow__(self, other, mod=None):
        return self._do_binaryop(other, lambda s, o: pow(o, s, mod))

    def __neg__(self):
        return self._do_unaryop(lambda s: -s)

    def __pos__(self):
        return self._do_unaryop(lambda s: +s)

    def __abs__(self):
        return self._do_unaryop(lambda s: abs(s))

    def __round__(self, n=0):
        return self._do_unaryop(lambda s: round(s, n))

    ##
    #  Utilities for working with Sentinels
    ##

    @staticmethod
    def get_key_for_max(inval):
        """Method for handling Sentinel in special fashion when generating key to use with max.

        Args:
            inval (object): The value to generate a key for.

        Returns:
            object: The appropriate key to force selection of sentinel if present; otherwise the inVal itself.
        """
        if isinstance(inval, NoDataSentinel):
            if inval.ignore:
                # configure to ignore
                return float('-inf')
            if inval.subVal is None:
                # configure to forward
                return float('inf')
            # forward sub
            return inval.subVal

        # if not a sentinel, forward as normal
        return float(inval)

    @staticmethod
    def get_key_for_min(inval):
        """Method for handling Sentinel in special fashion when generating key to use with min.

        Args:
            inval (object): The value to generate a key for.

        Returns:
            object: The appropriate key to force selection of sentinel if present; otherwise the inVal itself.
        """
        if isinstance(inval, NoDataSentinel):
            if inval.ignore:
                # configure to ignore
                return float('inf')
            if inval.subVal is None:
                # configure to forward
                return float('-inf')
            # forward sub
            return inval.subVal

        # if not a sentinel, forward as normal
        return float(inval)
