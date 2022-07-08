import os
import re
import keyword
import math
import builtins

from . import fuzzylogic as fl
from .nodata_handling import NoDataSentinel

class FLCombiner(object):
    """Utility for applying defuzzification operators and combining
    multiple decision spaces from fuzzy logic implications.


    Args:
        combineStr (str, optional): Default python equation for combining defuzzed values.Defaults to empty str.
        defaultDefuzz (str, optional): String identifier of operator used to defuzz an implication by default.
           Options are:
             - centroid: Use the centroid of the decision space. This is the default.
             - bisector: Use the bisector value of the decision space.
             - smallest_of_maximum: The smallest x-value of all values that correspond to the maximum y-value.
             - largest_of_maximum: The largest x-value of all values that correspond to the maximum y-value.
             - mean_of_maximum: The mean of all x-values that correspond to points at the maximum y-value.

    Keyword Args:
        defuzzDict (dict): Dictionary with a Fuzzy Logic set name as the key, and the defuzz operator
           to apply as the value. The valid defuzz values are identical to those listed for the defaultDefuzz
           argument.

    """

    def __init__(self, combinestr='', default_defuzz='centroid', **kwargs):

        self._expectedImps = kwargs['expected'] if 'expected' in kwargs else None
        self.parselogic(combinestr)
        self._defaultDefuzz = default_defuzz
        self._defuzzOps = {}
        if 'defuzzDict' in kwargs:
            self._defuzzOps = kwargs['defuzzDict']

    def set_defuzz_for_implication(self, impname, opname):
        """
        Set the defuzz operator to use for a specific implication.

        Args:
            impname (str): The name of the fuzzy logic set to apply the defuzz operator to.
            opname (str): The key for the centroid operator. See the 'defaultDefuzz' in the
              class argument list.

        """

        self._defuzzOps[impname] = opname

    def parselogic(self, evalstr, refresh=False):
        """
        Parse the logic from instructions on how to combine defuzzed values.

        Args:
            evalstr (str): The string of python logic to evaluate.
            refresh (bool, optional): If true, likely implication names will be extracted evalStr.
              This is useful for error checking. Defaults to False.

        """

        # check for expected implications. If it hasn't been defined yet,
        # assume all named variables in the evalstr are implications.
        if refresh is True or self._expectedImps is None:
            # this should split on all non-valid python labels.
            # it won't catch reserve words, but we can worry about that later
            rawlist = re.findall('[_a-zA-Z][_a-zA-Z0-9.]*', evalstr) if len(evalstr) > 0 else []

            # remove any keywords or builtins
            bilist = dir(builtins)
            self._expectedImps = [x for x in rawlist if not keyword.iskeyword(x) and x not in bilist]

        # we can extend this eventually, but for now assume its valid python
        self._comboLogic = evalstr

    def evaluate(self, implications, envargs=None, defuzzargs=None):
        """Evaluate the defuzzification operations and combining logic.

        Args:
            implications (dict): Dictionary of implications to act upon.
            envargs (dict,optional): Additional arguments to pass to the execution environment.
            defuzzargs (list,optional): Additional arguments to pass on to defuzzification operations.

        Returns:
            float: A number value representing the combined defuzzed values.

        Raises:
            fuzzylogic.FuzzyNoValError: If an expected implication is not found in implications, or if the implication
              processing encountered a fuzzy logic-specific error.
        """

        # find the defuzzed values for each implication
        if envargs is None:
            envargs = {}
        if defuzzargs is None:
            defuzzargs = []
        env_vars = dict({  # disable builtins for securityreasons
                         'builtins': None,
                         '__builtins__': None,
                         'checknodata': self.__class__.nodata_op,
                         # replacements for built ins
                         'max': self.__class__.maxop,
                         'min': self.__class__.minop,
                         'sum': self.__class__.sumop,
                         'product': self.__class__.prodop,
                         'gamma': self.__class__.gammaop,
                         # white-list math functions
                         'abs': builtins.abs,
                         'round': builtins.round,
                         'pow': builtins.pow,
                         'float': builtins.float,
                         'int': builtins.int,
                         'acos': math.acos,
                         'acosh': math.acosh,
                         'asin': math.asin,
                         'asinh': math.asinh,
                         'atan': math.atan,
                         'atan2': math.atan2,
                         'atanh': math.atanh,
                         'ceil': math.ceil,
                         'degrees': math.degrees,
                         'e': math.e,
                         'exp': math.exp,
                         'floor': math.floor,
                         'inf': math.inf,
                         'log': math.log,
                         'log2': math.log2,
                         'log10': math.log10,
                         'pi': math.pi,
                         'radians': math.radians,
                         'sin': math.sin,
                         'sinh': math.sinh,
                         'sqrt': math.sqrt,
                         'tan': math.tan,
                         'tanh': math.tanh
                        },
                        **envargs)

        for k in self._expectedImps:
            if k not in implications:
                raise fl.FuzzyNoValError('missing implication key')

        # use specific defuzzifier, if specified, or the default
        for key, imp in implications.items():
            if isinstance(imp, fl.FuzzyImplication):
                defuzzop = self._defuzzOps[key] if key in self._defuzzOps else self._defaultDefuzz
                dret = getattr(imp, defuzzop)(*defuzzargs)
                # dret should either be a Pt2D or a NoDataSEntinel
                # If Pt2D, assign x-value.
                if dret is None:
                    # if the result of the defuzz process is undefined, set to zero
                    env_vars[key] = 0.0
                elif not isinstance(dret, NoDataSentinel):
                    env_vars[key] = dret.x
                else:
                    env_vars[key] = dret
            else:
                env_vars[key] = imp  # presently should be float

        # aggregate according to rules and defuzzed values.
        dbg = eval(self._comboLogic, env_vars)
        return dbg

    def cleardefuzzforimplication(self, impl):
        """Clear the defuzzification operator applied to a specific implication.

        Args:
            impl (str): The name of the implication to clear.

        """
        if impl in self._defuzzOps:
            self._defuzzOps.pop(impl)

    def defuzzop_for_implication(self, impl, ret_default=False):
        """Retrieve the defuzzification operator for a specific implication.

        Args:
            impl (str): The name of the implication to query.
            ret_default (bool, optional): Only effects implications assigned to the default operator;
               Return the default defuzz operator if True, or None if False. Defaults to False.

        Returns:
            str: The identifier of the defuzz operator of the implication.
            None: If the implication uses the default operator and retDefault is False.
        """
        ret = None if not ret_default else self._defaultDefuzz

        if impl in self._defuzzOps:
            ret = self._defuzzOps[impl]

        return ret

    @property
    def found_implication_names(self):
        """list: A list of names of the implications expected to be passed in during evaluation."""
        return self._expectedImps[:]

    @staticmethod
    def nodata_op(val, isval, isnotval=None):
        """ Checks if a variable is a `NO DATA` value and returns the appropriate value.

        Args:
            val (float): The value to evaluate for `NO DATA`.
            isval (float): The value to return if ``val`` is `NO DATA`.
            isnotval (float, optional): The value to return if ``val`` is not `NO DATA`

        Returns:

        """

        if isinstance(val, NoDataSentinel):
            return isval

        if isnotval is not None:
            return isnotval
        return val

    @staticmethod
    def maxop(lhs, rhs, *args, **kwargs):
        """Overload of built-in max to properly handle the presence of a nodata sentinel.

        Notes:
            The kwargs will be ignored, relying instead on our function.

        Args:
            lhs (object): The first argument to check.
            rhs (object): The second argument to check.
            *args: Additional values to compare.
            **kwargs: ignored.

        Returns:
            object: The greater of the two objects, incorporating knowledge of the sentinels, if any present.
        """

        return builtins.max(lhs, rhs, *args, key=NoDataSentinel.get_key_for_max)

    @staticmethod
    def minop(lhs, rhs, *args, **kwargs):
        """Overload of built-in min to properly handle the presence of a nodata sentinel.

        Notes:
            The kwargs will be ignored, relying instead on our function.

        Args:
            lhs (object): The first argument to check.
            rhs (object): The second argument to check.
            *args: Additional values to compare.
            **kwargs: ignored.

        Returns:
            object: The lesser of the two objects, incorporating knowledge of the sentinels, if any present.
        """

        return builtins.max(lhs, rhs, *args, key=NoDataSentinel.get_key_for_min)

    @staticmethod
    def sumop(*args):
        """Standard sum operator.

        Args:
            *args: Values to sum together.

        Returns:
            number: The total of all combined values of args.
        """
        return builtins.sum(args)

    @staticmethod
    def prodop(*args):
        """Standard product operator.

        Args:
            *args: The values to multiply together.

        Returns:
            number: The product of all combined values in args.
        """
        if len(args) == 0:
            return 0
        tot = 1
        for a in args:
            tot *= a
        return tot

    @staticmethod
    def gammaop(gammaval, *args):
        """Gamma operator mimicing the Fuzzy Logic equivalent.

        Args:
            gammaval (number): Value in the range of [0,1].
            *args: The values to evaluate using the gamma value.

        Returns:
            The results of the gamma operation.

        Raises:
            ValueError: If gammaval is not in the range of [0,1].
        """
        if not (0 <= gammaval <= 1):
            raise ValueError('gamma value must be in range [0,1]; value supplied is {}'.format(gammaval))
        sumval = FLCombiner.sumop(args)
        prodval = FLCombiner.prodop(args)
        return (sumval**gammaval)*(prodval**(1.0-gammaval))
