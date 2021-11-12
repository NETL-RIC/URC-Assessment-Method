"""Contains classes used for storing and manipulating model data.

External Dependencies:
    * `numpy <http://www.numpy.org/>`_
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
from .compat2or3 import dict_iteritems, builtins
from ..fuzzylogic import fuzzylogic as fl
from ..fuzzylogic.nodata_handling import NoDataSentinel
import json
import os
import re
import keyword
import math


class SimpaException(Exception):
    """Simple exception intended to be raised by SIMPA related errors.

    Args:
        *args: Variable length argument list for parent Exception class.

    Keyword Args:
        simpaObj (object): SIMPA model object to associate with the Exception.
        isWarning (bool): Designate whether the Exception should be treated as warning or error.
    """

    def __init__(self, *args, **kwargs):

        self._simpaObj = None
        self._isWarning = False
        if 'simpaObj' in kwargs:
            self._simpaObj = kwargs['simpaObj']
        if 'isWarning' in kwargs:
            self._isWarning = kwargs['isWarning']

        Exception.__init__(self, *args)


######################################################################################################################

class DataContainer(object):
    """Base class for storing spatial data to be used as input.

    Args:
        name: The name to apply to the dataset.

    Keyword Args:
        transform (tuple): The Geo-transformation to assign.
        projection (str): WKT string describing projection to apply.
        noVal (number): The sentinel value used to designate a no-data value.

    """

    def __init__(self, name, **kwargs):
        self._name = name
        self._transform = None
        self._projection = None
        self._noVal = -99999.

        if 'transform' in kwargs:
            self._transform = kwargs['transform']
        if 'projection' in kwargs:
            self._projection = kwargs['projection']

        if 'noVal' in kwargs:
            self._noVal = kwargs['noVal']

    @property
    def geotransform(self):
        """tuple: Geo-transformation values; read-only."""
        return self._transform

    @property
    def projection(self):
        """str: WKT string describing the projection used; read-only."""
        return self._projection

    @property
    def name(self):
        """str: The name of the dataset; read-only."""
        return self._name

    @property
    def nodata_value(self):
        """number: Numeric flag specifying a cell with no data; read-only."""
        return self._noVal


######################################################################################################################

class GriddedData(DataContainer):
    """Container for storing gridded/raster data.

    Args:
        name: The name to apply to the dataset.

    Keyword Args:
        transform (tuple): The Geo-transformation to assign.
        projection (str): WKT string describing projection to apply.
        noVal (number): The sentinel value used to designate a no-data value.
        data (numpy.ndarray): A 2D array of values.
        rows (int): The number of rows to initialize.
        cols (int): THe number of columns to initialize.
    Raises:
        ValueError: If ``data`` is present, but not a two-dimensional numpy.ndarray.
        ValueError: If ``data`` is absent, and only ``rows`` or only ``cols`` are passed in as keyword arguments.
    """

    def __init__(self, name, **kwargs):

        DataContainer.__init__(self, name, **kwargs)

        if 'data' in kwargs:
            d = kwargs['data']
            if not isinstance(d, np.ndarray):
                raise ValueError("'data' must be a 2D numpy array object.")
            elif len(d.shape) != 2:
                raise ValueError("'data' must be two-dimensional.")
            self._data = d

        elif 'rows' in kwargs or 'cols' in kwargs:
            try:
                self._data = np.full((kwargs['rows'], kwargs['cols']), self._noVal)
            except KeyError as ke:
                raise ValueError('Key "' + ke.args[0] + '" missing; both "rows" and "cols" must be used together.')

    @property
    def shape(self):
        """tuple: The shape of the internal data container."""
        return self._data.shape

    def __getitem__(self, item):

        return self._data[item]


######################################################################################################################

class SparseData(DataContainer):
    """Data container for sparse/vector data.

    Notes:
        This is presently just a stub.
    """

    def __init__(self):
        DataContainer.__init__(self)
        # self.xs
        # self.ys
        # self.vals


######################################################################################################################

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
        for key, imp in dict_iteritems(implications):
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
        sumval = self.__class__.sumop(args)
        prodval = self.__class__.prodop(args)
        return (sumval**gammaval)*(prodval**(1.0-gammaval))


######################################################################################################################
# methods for loading/saving combiners
def serialize_combiner(combiner):
    """Generate a serializable representation of a FLCombiner object.

    Args:
        combiner (FLCombiner): The FLCombiner to generate a serializable representation for.

    Returns:
        dict: Data suitable for storing in a serialized container.
    """
    root = {'pyType': 'FLCombiner',
            'combineStatement': combiner._comboLogic}
    if combiner._defaultDefuzz is not None:
        root['defaultDefuzzOperator'] = combiner._defaultDefuzz

    if len(combiner._defuzzOps) > 0:
        root['defuzzOperators'] = combiner._defuzzOps

    return root


def deserialize_combiner(invals):
    """Generate a FLCombiner from a serialized representation.

    Args:
        invals (dict): Serialized representation of the FLCombiner to generate.

    Returns:
        FLCombiner: The FLCombiner described by inVals.
    """
    ret = FLCombiner(invals['combineStatement'])
    if 'defaultDefuzzOperator' in invals:
        ret._defaultDefuzz = invals['defaultDefuzzOperator']

    if 'defuzzOperators' in invals:
        ret._defuzzOps = invals['defuzzOperators']
    return ret


def load_flcombiner(inpath):
    """Load a FLCombiner from a json-compatible file.

    Args:
        inpath (str): The path to the file to load.

    Returns:
        FLCombiner: The FLCombiner as described by the file at inPath.
    """
    ret = None
    with open(inpath, 'r') as inFile:
        return deserialize_combiner(json.load(inFile))


def save_flcombiner(outpath, combiner):
    """Save a FLCombiner to a json-compatible file.

    Args:
        outpath (str): Path to the location to save the FLCombiner.
        combiner (FLCombiner): The FLCombiner to save to disk.

    """

    with open(outpath, 'w') as outFile:
        json.dump(outFile, serialize_combiner(combiner))


######################################################################################################################

class FLData(object):
    """Container for storing the combined fuzzylogic.FuzzyLogicSet and FLCombiner objects.

    Args:
        flSets (dict, optional): Name-value pairs of fuzzylogic.FuzzyLogicSet objects to include. Defaults
          to empty dict.
        combiners (dict, optional): Name-value pairs of FLCombiner objects to include. Defaults to empty
          dict.

    Attributes:
        flSets (dict): Dictionary of fuzzylogic.FuzzyLogicSet objects keyed by name.
        combiners (dict): Dictionary of FLCombiner objects keyed by name.
    """

    def __init__(self, flsets=None, combiners=None):

        if flsets is None:
            flsets = {}
        if combiners is None:
            combiners = {}
        self.flsets = flsets
        self.combiners = combiners

    def add_fuzzyset(self, name, flset):
        """Add a Fuzzy Logic Set to the FLData object.

        Args:
            name (str): The identifier of flSet.
            flset (fuzzylogic.FuzzyLogicSet): The fuzzylogic.FuzzyLogicSet to include.
        """
        self.flsets[name] = flset

    def add_combiner(self, name, combiner):
        """Add a Fuzzy Logic Combiner to the FLData object.

        Args:
            name (str): The identifier of combiner.
            combiner (FLCombiner): The FLCombiner to include.
        """
        self.combiners[name] = combiner

    def load_data(self, flpaths, combpaths):
        """Load FLData components from one or more listed files.

        Args:
            flpaths (list): Path to all fuzzylogic.FuzzyLogicSet files to load.
            combpaths (list): Path to all FLCombiner files to load.

        Returns:
            list: A list of errors if any errors that occurred.
            None: If no errors occurred.
        """

        errs = []
        res = self.load_flsets(flpaths)
        if res is not None:
            errs += res
        res = self.load_combiners(combpaths)
        if res is not None:
            errs += res

        return errs if len(errs) > 0 else None

    def load_flsets(self, flpaths):
        """Load Data for one or more fuzzylogic.FuzzyLogicSets files.

        Args:
            flpaths (list): Path to all fuzzylogic.FuzzyLogicSet files to load.

        Returns:
            list: A list of errors if any errors that occurred.
            None: If no errors occurred.
        """

        errs = []

        self.flsets.clear()

        for p in flpaths:
            try:
                key = os.path.splitext(os.path.basename(p))[0]
                storage = fl.FLSettings.LoadSettings(p)
                self.flsets[key] = storage['fuzzset']
                self.flsets[key].import_rules(storage['fuzzset'].rules_string.split('\n'))
            except Exception:
                errs.append("FuzzySet at '" + p + "' failed to load.")

        return errs if len(errs) > 0 else None

    def load_combiners(self, combpaths):
        """Load Data for one or more FLCombiner files.

        Args:
            combpaths (list): Path to all FLCombiner files to load.

        Returns:
            list: A list of errors if any errors that occurred.
            None: If no errors occurred.
        """

        errs = []
        self.combiners.clear()

        for p in combpaths:
            try:
                key = os.path.splitext(os.path.basename(p))[0]
                self.combiners[key] = load_flcombiner(p)
            except Exception:
                errs.append("FLCombiner at '" + p + "' failed to load.")

        return errs if len(errs) > 0 else None

    @staticmethod
    def fldata_from_files(flpaths, combpaths):
        """Generate a FLData object from one or more listed files.

        Args:
            flpaths (list): Path to all fuzzylogic.FuzzyLogicSet files to load.
            combpaths (list): Path to all FLCombiner files to load.

        Returns:
            tuple: With the following fields:
              0. The FLData object.
              1. list: A list of strs describing any encountered errors.
                 None: If no errors encountered.
        """

        ret = FLData()
        errs = ret.load_data(flpaths, combpaths)
        return ret, errs
