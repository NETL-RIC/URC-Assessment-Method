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
            return 'ignored'
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
        if self.ignore or self.subVal is None:
            return self  # None

        return self.subVal+other

    def __sub__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return self.subVal - other

    def __mul__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return self.subVal * other

    def __truediv__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return self.subVal / other

    def __floordiv__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return self.subVal // other

    def __mod__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None
        return self.subVal % other

    def __divmod__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return divmod(self.subVal, other)

    def __pow__(self, other, modulo=None):
        if self.ignore or self.subVal is None:
            return self  # None

        return pow(self.subVal, other, modulo)

    def __radd__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return other + self.subVal

    def __rsub__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return other - self.subVal

    def __rmul__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return other * self.subVal

    def __rdiv__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return other / self.subVal

    def __rfloordiv__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return other // self.subVal

    def __rmod__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None

        return other % self.subVal

    def __rdivmod__(self, other):
        if self.ignore or self.subVal is None:
            return self  # None
        return divmod(other, self.subVal)

    def __rpow__(self, other, mod=None):
        if self.ignore or self.subVal is None:
            return self  # None

        return pow(other, self.subVal, mod)

    def __neg__(self):
        if self.ignore or self.subVal is None:
            return self  # None
        return -self.subVal

    def __pos__(self):
        if self.ignore or self.subVal is None:
            return self  # None
        return +self.subVal

    def __abs__(self):
        if self.ignore or self.subVal is None:
            return self  # None

        return abs(self.subVal)

    def __round__(self, n=0):
        if self.ignore or self.subVal is None:
            return self  # None
        return round(self.subVal, n)

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
