"""Module containing classes for interpreting and evaluating
Fuzzy Logic rules.

Author: Patrick Wingo

Version: 0.1

Attributes:
    noDataValue (float): Value used to represent a no-data value.
"""

from __future__ import absolute_import, division, print_function, unicode_literals
from .fuzzycurves import *

noDataValue = -99999.

#######################################################################


class FuzzyError(Exception):
    """Error raised by FuzzyLogic issues.

    Errors raised by classes and logic within this module should either use
    or inherit from this class. This will allow users of this module to
    distinguish from exceptions raised from other processes.
    """
    
    @property
    def message(self):
        """str: Retrieve the message associated with this exception.
        """
        return str(self.args[0])


class FuzzyNoValError(FuzzyError):
    """Simple error for documenting when a no-value issue is encountered in the fuzzy logic routines."""
    pass

#######################################################################


class FuzzyValue(object):
    """Class representing a fuzzy value's truth statement and equivalent numeric value.

    Attributes:
        truthstatement (str): The read-only statement representation of the value.
        truthValue (float): The numeric value.

    Args:
        statement (str): The string value representing the value.
        value (float): The mathematical value; integer or float.
    """

    # NOTE: it would be good to add boolean operators that work directly
    # with floats so outside code does not have to rely on float casting.
    def __init__(self, statement, value):

        self._tStat = statement
        self.truthValue = value

    # cast
    def __float__(self):

        # value to convert to when using float() operator to convert
        return float(self.truthValue)

    def __repr__(self):

        return self._tStat+": "+str(self.truthValue)

    @property
    def truthstatement(self):
        """str: The statement of truth.
        """
        return self._tStat

    def __add__(self, other):
        return self.truthValue+other

    def __sub__(self, other):
        return self.truthValue-other

    def __mul__(self, other):
        return self.truthValue*other

    def __truediv__(self, other):
        return self.truthValue/other

    def __floordiv__(self, other):
        return self.truthValue//other

    def __mod__(self, other):
        return self.truthValue % other

    def __divmod__(self, other):
        return divmod(self.truthValue,other)

    def __pow__(self, other, modulo=None):
        return pow(self.truthValue, other, modulo)

    def __radd__(self, other):
        return other+self.truthValue

    def __rsub__(self, other):
        return other-self.truthValue

    def __rmul__(self, other):
        return other*self.truthValue

    def __rdiv__(self, other):
        return other/self.truthValue

    def __rfloordiv__(self, other):
        return other//self.truthValue

    def __rmod__(self, other):
        return other % self.truthValue

    def __rdivmod__(self, other):
        return divmod(other,self.truthValue)

    def __rpow__(self, other, mod=None):
        return pow(other, self.truthValue, mod)

    def __neg__(self):
        return -self.truthValue

    def __pos__(self):
        return +self.truthValue

    def __abs__(self):
        return abs(self.truthValue)

    def __round__(self, n=0):
        return round(self.truthValue, n)


#######################################################################


class FuzzyRule(object):
    """Represents a FuzzyRule to be evaluated.

    A common-language syntax is supported, which is then compiled into Python and 
    executed, Returning a FuzzyImplication object representing the decision space.

    Attributes:
        result (FuzzyResult): Result object referenced by the fuzzy rule.
    """


    CONTROL_WORDS = ('IF', 'DEF', 'IS', 'THEN')
    OPERATOR_WORDS = ('AND', 'OR', 'XOR', 'NOT',
                      'SUM', 'PRODUCT', 'GAMMA')

    def __init__(self):
        """ """
        self._inputs = {}
        self._ruleStr = None
        self.result = None
        self._execStatement = 'None'
        self._inpQueryTable = None
        self._result_mf = None

    def __repr__(self):
        return 'Inputs: {0} \nResults: {1} \nCompiled statement: {2}'.format(len(self._inputs), len(self.result) if self.result is not None else 'N/A',
                                                                             self._execStatement)

    def __str__(self):
        return self._ruleStr

    def add_input(self, fin):
        """Add a FuzzyInput object for evaluation.

        In order for a rule to execute properly, it must be aware of the inputs, which
        are looked up by name. Any FuzzyInput object added to the FuzzyRule will overwrite
        any previous entries with the same name.
        
        Args:
            fin (FuzzyInput): The FuzzyInput object to add.
        """
        self._inputs[fin.name] = fin

    def clear_inputs(self):
        """Removes all stored FuzzyInputs from the rule."""
        self._inputs.clear()

    def evaluate_rule(self, invals):
        """ Evaluate Rule, using inVals dict for variable values.
    
        This method assumes that build_rule_from_string() has been previously called.
        
        Args:
            invals: A dictionary of values to apply to input responses curves. There should be
                one entry for each FuzzyInput using the same key; the value for each record should be a number or
                FuzzyValue.
                
        Returns:
            FuzzyImplication: represents the decision space.
            None: If build_rule_from_string() has not been previously called.
        """
        
        # The global environment needs:
        # self: For referencing associated inputs and results.
        # invals: For the values to apply to each input.
        # FuzzyRule: For static methods used as operators.
        envdict = dict(_result=self.result, _inputs=self._inputs, inVals=invals,
                       **{v.__name__: v for v in dict(**FuzzyRule.unary_op_map(),
                                                      **FuzzyRule.binary_op_map(),
                                                      **FuzzyRule.fn_map()).values()},)

        return eval(self._execStatement, envdict)

    def build_rule_from_string(self, instr, alias_dict=None):
        """ Take grammar and convert to string of logic that can be executed by Python.

        The resulting Python code will be stored as part of the FuzzyRule object.

        The following words are Reserved, and are case-insensitive:

            ======== ============================================
            Reserved Description
            ======== ============================================
            IF       beginning of statement
            DEF      for defining an alias/macro/variable statement
            IS       from input to value
            THEN     end of statement to result select
            ________ ____________________________________________
            AND      binary operator
            OR       binary operator
            XOR      binary operator
            NOT      unary operator (should occur after is)
            ________ ____________________________________________
            PRODUCT  Product operator
            SUM      SUM Operator (bounded to [0,1])
            GAMMA    GAMMA Operator
            ======== ============================================

        Args:
            instr (str): The string that should be evaluated as a rule.
            alias_dict (dict,optional): Dictionary of alias names mapped to associated logic.

        Raises:
            FuzzyError: If a syntax error is encountered; check the "message" attribute for the reason.
        """

        # TODO: test grammar check

        impstr = '_result.get_implication("{1}",{2})'

        # cache rule string for reference
        self._ruleStr = instr

        # replace '=' with IS since they are synonymous
        process_str = instr.replace('=', ' is ')

        # ensure operators are tokened
        to_buff = ['(', ')', ',']
        for t in to_buff:
            process_str = process_str.replace(t, ' '+t+' ')

        # create list of token strings
        tokens = process_str.split()

        # check if
        if tokens[0].lower() != 'if':
            raise FuzzyError('"IF" must begin rule')

        # chomp if
        tokens[0:1] = []

        to_result = None
        # split on then
        for i in range(len(tokens)):
            if tokens[i].lower() == 'then':
                to_result = tokens[i+1:]
                tokens = tokens[:i]
                break
        if to_result is None:
            raise FuzzyError('"THEN" keyword missing from rule')
        if len(to_result) != 3:
            raise FuzzyError('Malformed THEN clause')

        self._result_mf = to_result[2]

        self._inpQueryTable = {}
        condition = FuzzyRule._parse_tokens(tokens, self._inpQueryTable, alias_dict)

        # Convert result (toRes) statement
        # for now, assume toRes has 3 values
        # save python execution statement
        self._execStatement = impstr.format(to_result[0], to_result[2], condition)

    @staticmethod
    def build_alias_from_string(instr, alias_dict=None):
        """Take grammer and convert to string of logic that can be substituted as an alias or macro.

        Args:
            instr (str): The string that should be evaluated as an alias definition.
            alias_dict (dict,optional): Dictionary of alias names mapped to associated logic.

        Returns:
            tuple: The name of the alias, and the associated logic.
        """

        # replace '=' with IS since they are synonymous
        process_str = instr.replace('=', ' is ')

        # ensure operators are tokened
        to_buff = ['(', ')', ',']
        for t in to_buff:
            process_str = process_str.replace(t, ' ' + t + ' ')

        # create list of token strings
        tokens = process_str.split()

        # check if
        if tokens[0].lower() != 'def':
            raise FuzzyError('"DEF" must begin alias')

        is_loc = tokens.index('is')
        if len(tokens) < 4 and is_loc != 2:
            raise FuzzyError('Malformed "DEF" statement; format should be "DEF <label> [is|=] <statements>"')
        identifier = tokens[1]
        logic = FuzzyRule._parse_tokens(tokens[3:], aliases=alias_dict)

        # return name of variable and logic associated
        return identifier, logic

    @staticmethod
    def unary_op_map():
        return {'not':FuzzyRule.notop}

    @staticmethod
    def binary_op_map():
        return {'and': FuzzyRule.andop, 'or':FuzzyRule.orop, 'xor':FuzzyRule.xorop}

    @staticmethod
    def fn_map():
        return {'product':FuzzyRule.productop, 'sum':FuzzyRule.sumop, 'gamma':FuzzyRule.gammaop}

    @staticmethod
    def _parse_tokens(tokens, inp_query_map=None, aliases=None):
        """Derive Python logic from a list of tokens.

        Args:
            tokens (list): strs with values representing syntactic tokens.
            inp_query_map (dict,optional): dict to populate with input mappings.
            aliases (dict,optional): alias macros to insert into if statement.
        Returns:
            str: Python code as described by the tokens.

        """
        # format strings
        assignstr = '_inputs["{0}"].truth_for_statement(inVals["{0}"],"{1}")'
        notstr = 'not({0})'
        boolstr = '{0}({1},{2})'
        funcstr = '{0}{1}'

        # mappings
        bool_ops = {k : v.__name__ for k,v in FuzzyRule.binary_op_map().items()}
        func_ops = {k : v.__name__ for k,v in FuzzyRule.fn_map().items()}

        # process parens first
        # check for equal number of parens
        lparen_count = 0
        rparen_count = 0
        for c in tokens:
            if c == '(':
                lparen_count += 1
            elif c == ')':
                rparen_count += 1

        if lparen_count > rparen_count:
            raise FuzzyError('Paren mismatch: more "(" than ")"')
        elif lparen_count < rparen_count:
            raise FuzzyError('Paren mismatch: more ")" than "("')

        i = 0
        while i < len(tokens):
            if tokens[i] == '(':
                start = i
                end = FuzzyRule._find_matching_paren(tokens, i)
                # omit parens to avoid infinite loop, but retain for result
                tokens[start:end+1] = ['(' + FuzzyRule._parse_tokens(tokens[start + 1:end], inp_query_map, aliases) + ')']
            i += 1

        # Apply aliases as encountered
        if aliases is not None:
            i = 0
            while i < len(tokens):
                if tokens[i].lower() in aliases:
                    tokens[i] = '('+aliases[tokens[i].lower()]+')'
                i += 1

        # Apply Functions after paren processing
        i = 0
        while i < len(tokens):
            if tokens[i].lower() in func_ops:
                tokens[i:i+2] = [funcstr.format(func_ops[tokens[i].lower()], tokens[i+1])]
            i += 1

        # with parens processed, check for proper grammar
        reservedlist = ['is', 'not', 'then', 'if', 'def', ','] + list(bool_ops.keys()) + list(func_ops.keys())
        lastreserved = True  # represents 'if'
        for i, token in enumerate(tokens):
            isreserved = token[0] != '(' and token.lower() in reservedlist
            if isreserved == lastreserved:
                # special case: IS NOT
                if tokens[i-1].lower() == 'is' and tokens[i].lower() == 'not':
                    continue
                raise FuzzyError('Bad Grammar: ?'+('IF' if i == 0 else tokens[i-1])+' '+tokens[i]+'?')
            lastreserved = isreserved

        # find not operators and move
        for i in range(len(tokens)):
            if tokens[i].lower() == 'not':
                tmp = tokens.pop(i)
                tokens.insert(i - 2, tmp)

        # Collapse is statements into table calls
        i = 0
        while i < len(tokens):
            if tokens[i].lower() == 'is':
                # construct new token via substitution
                newtoken = assignstr.format(tokens[i - 1], tokens[i + 1])

                # add input and membership function to lookup table for individual reference.
                if inp_query_map is not None:
                    inp_query_map[tokens[i - 1]] = tokens[i + 1]
                # assign new token, remove old
                tokens[i - 1] = newtoken
                tokens[i:i + 2] = []
            i += 1

        # Convert Not statements
        i = 0
        while i < len(tokens):
            if tokens[i].lower() == 'not':
                tokens[i] = notstr.format(tokens.pop(i + 1))
            i += 1

        # Apply booleans
        i = 0
        while i < len(tokens):
            if tokens[i].lower() in bool_ops:
                newtoken = boolstr.format(bool_ops[tokens[i].lower()], tokens[i - 1], tokens[i + 1])
                tokens[i - 1] = newtoken
                tokens[i:i + 2] = []
            else:
                i += 1

        return " ".join(tokens)

    def memberfunc_for_input(self, inpname):
        """Retrieve the membership function name for the given rule.

        Args:
            inpname (str): The name of the input variable to query.

        Returns:
            str: The name of the selected membership function.

        Raises:
            FuzzyError: If method is called before build_rule_from_string.
            KeyError: If input is not represented in rule.

        See Also:
            FuzzyRule.build_rule_from_string.
        """
        if not self._inpQueryTable:
            raise FuzzyError('"build_rule_from_string()" must be called before "memberfunc_for_input"')

        return self._inpQueryTable[inpname]

    def memberfunc_for_result(self):
        """Retrieve the member function from the associated result.

        Returns:
            str: The name of the membership function.

        Raises:
            FuzzyError: If method is called before build_rule_from_string.

        See Also:
            FuzzyRule.build_rule_from_string.

        """
        if not self._result_mf:
            raise FuzzyError('"build_rule_from_string()" must be called before "memberfunc_for_result"')
        return self._result_mf

    def value_for_input(self, inpname, inval):
        """

        Args:
            inpname (str): The name of the input variable to query.
            inval (float): The input value to retrieve a value for.

        Returns:
            float: The appropriate value for inval.

        Raises:
            FuzzyError: If method is called before build_rule_from_string.
            KeyError: If input is not represented in rule.

        See Also:
            FuzzyRule.build_rule_from_string.
        """

        mfname = self.memberfunc_for_input(inpname)
        return self._inputs[inpname].truth_for_statement(inval, mfname)

    @staticmethod
    def _find_matching_paren(tokens, start_parenind):

        hitcount = 1
        for i in range(start_parenind + 1, len(tokens)):
            if tokens[i] == '(':
                # internal paren group
                hitcount += 1
            elif tokens[i] == ')':
                # not end of paren group
                hitcount -= 1
                if hitcount == 0:
                    # found it
                    return i

        # if we get here, we have an unmatched paren; that's bad
        raise FuzzyError('Paren mismatch; "(" without matching ")"')

    @staticmethod
    def reserved_words():
        """Retrieve a list of all words that are reserved for specific uses.

        All reserved words are evaluated in a case-insensitive fashion.

        Returns:
            tuple: Lower-case versions of all reserved words.
        """
        return 'if', 'is', 'then', 'and', 'or', 'not', 'product', 'sum', 'gamma'

    # boolean truth operators
    @staticmethod
    def andop(lhs, rhs):
        """Fuzzy Logic AND operator.

        Args:
            lhs (FuzzyValue or float): The lefthand argument.
            rhs (FuzzyValue or float): The righthand argument.

        Returns:
            float: The minimum of the lhs and rhs values.
        """

        return min(lhs, rhs, key=NoDataSentinel.get_key_for_min)

    @staticmethod
    def orop(lhs, rhs):
        """Fuzzy Logic OR operator.

        Args:
            lhs (FuzzyValue or float): The lefthand argument.
            rhs (FuzzyValue or float): The righthand argument.

        Returns:
            float: The maximum of the lhs and rhs values.
        """
        return max(lhs, rhs, key=NoDataSentinel.get_key_for_max)

    @staticmethod
    def xorop(lhs, rhs):
        """Fuzzy Logic XOR operator.

        Args:
            lhs (FuzzyValue or float): The lefthand argument.
            rhs (FuzzyValue or float): The righthand argument.

        Returns:
            float: The value extracted from the derived exclusive-or relationship.
        """

        # quick function aliases to make this easier to read.
        andop =FuzzyRule.andop
        orop = FuzzyRule.orop
        notop =FuzzyRule.notop

        return andop(notop(andop(lhs, rhs)), orop(lhs, rhs))

    @staticmethod
    def notop(val):
        """Fuzzy Logic NOT operator.

        If the value is **NO DATA**, then the **NO DATA** value is returned.

        Args:
            val (FuzzyValue or float): Value to invert.

        Returns:
            float: 1 minus the value.
        """

        if isinstance(val, NoDataSentinel):
            return val
        return 1-float(val)

    @staticmethod
    def productop(*args):
        """ Fuzzy Logic PRODUCT Operator.

        **NO DATA** values are omitted from aggregation, if all values passed in are **NO DATA**, then **NO DATA**
        is returned.

        Args:
            *args: Two or more arguments as numbers or FuzzyValues.

        Returns:
            float: The product of all argmuments multiplied together.

        Raises:
            FuzzyError: If there are less than two arguments.
        """
        if len(args) < 2:
            raise FuzzyError('PRODUCT requires at least 2 arguments')

        prod = 1.0
        for p in args:
                prod *= p

        return prod

    @staticmethod
    def sumop(*args):
        """Fuzzy Logic SUM Operator.

        Follows logic found `here`_.

        **NO DATA** values are omitted from aggregation, if all values passed in are **NO DATA**, then **NO DATA**
        is returned.

        Args:
            *args: Two or more arguments as numbers or FuzzyValues.

        Returns:
            float: 1 minus the product of all arguments multiplied together.

        Raises:
            FuzzyError: If there are less than two arguments.

        .. _here: https://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-analyst-toolbox/how-fuzzy-overlay-works.htm\
        #ESRI_SECTION1_E4E9B3E5931A421DBD5B80991AEE9DB8
            """
        if len(args) < 2:
            raise FuzzyError('SUM requires at least 2 arguments')

        ret = FuzzyRule.productop(*[1.0 - a for a in args])
        return 1.0 - ret

    @staticmethod
    def gammaop(gamma, *args):
        """Fuzzy Logic GAMMA Operator.

        Follows logic found `here`_.

        If the ``gamma`` argument is **NO DATA**, then **NO DATA** is returned.

        **NO DATA** values are omitted from aggregation, if all values passed in are **NO DATA**, then **NO DATA**
        is returned.

        Args:
            gamma: The gamma value to apply, must be in the range [0,1].
            *args: Two or more arguments as numbers or FuzzyValues.

        Returns:
            float: The value derived by combining the args summed and multiplied, biased by the gamma value.

        Raises:
            FuzzyError: If there are less than two arguments, or if gamma is outsie the range of [0,1].

        .. _here: https://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-analyst-toolbox/how-fuzzy-overlay-works.htm\
        #ESRI_SECTION1_E4E9B3E5931A421DBD5B80991AEE9DB8
        """

        if gamma == noDataValue:
            return noDataValue

        if len(args) < 2:
            raise FuzzyError('GAMMA requires at least 2 arguments after the gamma value.')

        if 0.0 > gamma or gamma > 1.0:
            raise FuzzyError('Gamma value must be in the range [0,1]')

        sumval = FuzzyRule.sumop(*args)
        prodval = FuzzyRule.productop(*args)

        return (sumval**gamma)*(prodval**(1.0-gamma))

    @property
    def pythonlogic(self):
        return self._execStatement

    @property
    def inputlist(self):
        """list: fuzzylogic.FuzzyInput objects included in rule."""

        ret = [v for _, v in dict_iteritems(self._inputs)]
        ret.sort(key=lambda inp: inp.name)
        return ret

    @property
    def foundinputs(self):
        """list: names of inputs encountered during parsing"""
        if not self._inpQueryTable:
            raise FuzzyError('"build_rule_from_string()" must be called before "foundinputs"')
        return list(self._inpQueryTable.keys())

#######################################################################


class FuzzyInput(object):
    """A range and collection of truth curves/membership functions used as input for a fuzzy logic rule.

    Attributes:
        minval (float): The minimum value accepted by the input.
        maxval (float): The maximum value accepted by the input.
        name (str): The name of the input.

    Args:
        name (str): The name of the input.
        minval (float, optional): The minimum accepted value. Defaults to 0.
        maxval (float, optional): The maximum accepted value. Defaults to 1.
    """

    def __init__(self, name, minval=0, maxval=1):

        self._truthCurves = {}
        self.minval = minval
        self.maxval = maxval
        self.name = name

    def __repr__(self):
        return 'Name: {0}\nRange:{1}-{2}\nCurves: {3}'.format(self.name, self.minval,
                                                              self.maxval, len(self._truthCurves))

    def add_curve(self, curve):
        """Add a FuzzyCurve to use a membership function.

        Args:
            curve (FuzzyCurve): The FuzzyCurve to add. If another curve with the same name already exists,
                it will be overwritten.
        """

        self._truthCurves[curve.name] = curve

    def get_curve(self, name):
        """Retrieve a curve associated with the supplied truth statement/name.

        Args:
            name (str): The name of the curve to retrieve.

        Returns:
            FuzzyCurve: The FuzzyCurve with the supplied name.
        """

        return self._truthCurves[name]

    def replace_curve(self, name, crv):
        """Replace an existing curve with another.

        Args:
            name (str): The name of the curve to replace.
            crv (fuzzylogic.fuzzyCurves.FuzzyCurve): The FuzzyCurve to use as replacement.

        """
        self._truthCurves[name] = crv

    def pop_curve(self, name):
        """Remove and Retrieve a curve associated with the supplied truth statement.

        Args:
            name (str): The name of the curve to remove and retrieve.

        Returns:
            FuzzyCurve: The FuzzyCurve with the supplied name.
        """
        return self._truthCurves.pop(name)

    def truth_for_statement(self, value, membname):
        """Retrieve a fuzzy value that results from applying the supplied value to the supplied membership function.

        Args:
            value (float): The value to use for query.
            membname (str): The name of the membership function to query.

        Returns:
            FuzzyValue: The value returned by the membership function query.
        """

        epsilon = 1E-4
        if isinstance(value, NoDataSentinel):
            if value.ignore is True or value.subVal is None:
                return value
            value = value.subVal
        # if value<self.minval and abs(self.minval-value)<epsilon:
        #     value=self.minval
        # elif value>self.maxval and abs(value-self.maxval)<epsilon:
        #     value=self.maxval
        n = self._truthCurves[membname]((value - self.minval) / (self.maxval - self.minval))
        # clamp to accommodate rounding errors
        if n > 1.0 and abs(n-1.0) < epsilon:
            n = 1.0
        elif 0.0 > n > -epsilon:
            n = 0.0
        return FuzzyValue(membname, n)

    def curve_for_name(self, name):
        """ Retrieve the membership function curve with the supplied name.

        Args:
            name (str): The membership function to look for.

        Returns:
            FuzzyCurve: The curve associated with the supplied name.

        Raises:
            KeyError: If there are no curves associated with the supplied name.
        """
        return self._truthCurves[name]

    def refresh_curvekeys(self):
        """Resync any curve keys with their names as needed.
        """

        keys = list(self._truthCurves.keys())

        for k in keys:
            crv = self._truthCurves[k]
            if crv.name != k:
                # update key for curve
                self._truthCurves[crv.name] = crv
                self._truthCurves.pop(k)

    def curve_iter(self):
        for k,v in self._truthCurves.items():
            yield k,v

    @property
    def truthstrlist(self):
        """list: A list of truth curve names.
        """
        return [x for x in self._truthCurves.keys()]

    @property
    def curvecount(self):
        """int: The number of membership functions.
        """
        return len(self._truthCurves)

#######################################################################


class FuzzyImplication(object):
    """The implication that results from evaluating a rule.

    Implications can be combined to find the final solution space.

    Args:
        minval (float): The minimum value to apply to the implication.
        maxval (float): The maximum value to apply to the implication.
        theCurves (list): FuzzyCurves representing the implication region.
        yClips (list): zero or more y-values used to clip the curves.

    """

    def __init__(self, minval, maxval, curves, yclips):

        self._curves = curves
        self._minVal = minval
        self._maxVal = maxval
        self._yClips = yclips
        self._hasNDClip = False
        self._ignoreND = False

        for i,clip in enumerate(self._yClips):
            if isinstance(clip, NoDataSentinel):
                if clip.subVal is not None:
                    self._yClips[i] = clip.subVal
                else:
                    self._hasNDClip = True
                    self._ignoreND = self._ignoreND or clip.ignore

    def __repr__(self):
        return 'Range: {0}-{1}\n{2}'.format(self._minVal, self._maxVal, ','.join([s.__repr__() for s in self._curves]))

    def __add__(self, rhs):
        """Combines two implications.

        Args:
            rhs (FuzzyImplication): The FuzzyImplication to combine with this FuzzyImplication.

        Returns:
            FuzzyImplication: The combination of the supplied FuzzyImplications.
        """
        return FuzzyImplication.combine(self, rhs)

    def __call__(self, x):
        """

        Args:
            x (float): The lookup value to apply.

        Returns:
            float: The equivalent y-val for the matching x-val.
        """

        if self._hasNDClip:
            return NoDataSentinel(self._ignoreND)

        # normalize for curves
        n = (x - self._minVal) / (self._maxVal - self._minVal)
        maxret = 0.0
        for crv,clp in zip(self._curves,self._yClips):

            basey = crv(n)
            maxret = max(maxret, min(basey, clp))

        return maxret

    def getclip(self, ind):
        """Get a specific clip height.

        Args:
            ind (int): The index of the clip height to retrieve.

        Returns:
            float: The value of the requested clip height.

        Raises:
            IndexError: if ind is not a valid index.
        """
        return self._yClips[ind]

    def drawpoints(self, samplecount=1000):
        """Retrieve a list of normalized points for drawing the Implication curve.

        Args:
            samplecount (int,optional): The number of samples to use to build the curve; defaults to 1000.

        Returns:
            list: Pt2D objects representing the points used to approximate the implication curve.
        """
        pts = [Pt2D(0, 0) for _ in range(samplecount)]
        startx = self._minVal
        endx = self._maxVal
        valrange = endx - startx
        step = valrange / (samplecount - 1)
        # step = 1 / (samplecount - 1)
        for i in range(samplecount):
            fullx = (step * i) + startx
            pts[i].x = (fullx - startx) / valrange
            pts[i].y = self(fullx)

        return pts

    @staticmethod
    def combine(lhs, rhs):
        """combine two implications.

        Args:
            lhs (FuzzyImplication): The first FuzzyImplication to use in the combination.
            rhs (FuzzyImplication): The second FuzzyImplication to use in the combination.

        Returns:
            FuzzyImplication: The combination of lhs and rhs.

        Raises:
            FuzzyError: If the minimum and maximum values do not match between the FuzzyImplications.
        """
        if lhs._minVal != rhs._minVal or lhs._maxVal != rhs._maxVal:
            raise FuzzyError('Range of values must be the same when combining Implications')

        # if either implication has a no data ceiling, ignore and return the opposite.
        # if both have nd value than the implication will be forwarded on, and will always return
        if lhs._hasNDClip:
            return rhs

        if rhs._hasNDClip:
            return lhs

        # find segments that intersect and return
        return FuzzyImplication(lhs._minVal, lhs._maxVal, lhs._curves+rhs._curves, lhs._yClips+rhs._yClips)

    @property
    def minval(self):
        """float: The minimum value of the implication.
        """
        return self._minVal

    @property
    def maxval(self):
        """float: The maximum value of the implication.
        """
        return self._maxVal

    # -- Begin defuzzifiers

    def centroid(self, samplecount=1000):
        """Find the centroid for the implication for a non-zero decision space.

        Args:
            samplecount (int, optional): The number of samples to take when solving the integral. Defaults to 1000.

        Returns:
            noDataHandling.NoDataSentinel: If the implication has one or more noData clipping heights that
             is not associated with a substitution value.
            geomutils.Pt2D: The centroid if decision space is not empty.
            None: If the decision space is empty.
        """

        if self._hasNDClip:
            # assume no data substitution has already taken place.
            return NoDataSentinel(self._ignoreND)

        # The centroid will be found using the integral formula for a bounded region (what we have)
        # https://en.wikipedia.org/wiki/Centroid#Bounded_region
        # our f(x) is self._curve.y_for_x()
        # our g(x) is the zero line, so g(x)=0 all the time. This simplifies the math:
        # f(x)-g(x)== y == f(x)+g(x)

        # grab the x-bounds of the non-zero decision space
        startx = self.minval
        starty = self(startx)
        endx = self.maxval
        endy = self(endx)

        step = (endx-startx) / samplecount

        # delta x = (b-a/n)/3
        simp_coef = (step/3)

        area_sum_odds = 0.0
        area_sum_evens = 0.0
        x_sum_odds = 0.0
        x_sum_evens = 0.0
        y_sum_odds = 0.0
        y_sum_evens = 0.0

        for i in range(0, samplecount + 1):
            x = startx+(step*i)
            y = self(x)

            # Simpson's Rule for Integration
            # Calculate Area, Collect Xs, Ys
            # odd steps; excl. start point
            if i != 0 and i % 2 == 1:
                x_sum_odds += 4*(x*y)
                y_sum_odds += 4*(y**2)
                area_sum_odds += 4*y

            # even steps; excl. end point
            if i != samplecount and i % 2 == 0:
                x_sum_evens += 2*(x*y)
                y_sum_evens += 2*(y**2)
                area_sum_evens += 2*y

        # Apply Simpson's Rule for Xs
        # totx = simp_coef*(startx*starty + x_sum_odds + x_sum_evens + endx*endy)

        # Apply Simpson's Rule for Ys
        toty = simp_coef*1/2*(starty + y_sum_odds + y_sum_evens + endy)

        # Apply Simpson's Rule for Area
        totarea = simp_coef*(starty + area_sum_odds + area_sum_evens + endy)

        # no values, no centroid!
        if totarea == 0:
            return None

        # centroid
        return toty/totarea

    def bisector(self, samplecount=1000):
        """Defuzzify by finding the bisector of the area of the solution space.

        Based on definition found on the `mathworks site`_.

        .. _mathworks site: https://www.mathworks.com/help/fuzzy/examples/defuzzification-methods.html

        Args:
            samplecount (int, optional): The number of samples to take when solving the integral. Defaults to 1000.

        Returns:
            noDataHandling.NoDataSentinel: If the implication has one or more noData clipping heights that
             is not associated with a substitution value.
            geomutils.Pt2D: The x-coordinate along the bisector, and the y coordinate along the maximum y value
              along the bisector, if solution space is not empty.
            None: If the solution space is empty.

        Raises:
            FuzzyError: If the solution space is not empty, but a bisect could not be calculated.
        """

        if self._hasNDClip:
            # assume no data substitution has already taken place.
            return NoDataSentinel(self._ignoreND)

        # grab the x-bounds of the non-zero decision space
        startx = self.minval
        endx = self.maxval

        step = (endx-startx) / samplecount

        cumu_forward_totarea = 0.0
        cumu_backward_totarea = 0.0

        # put some space aside. Use empty so we don't waste time running through the arrays here
        # (each entry will be assigned in the next loop)
        forward_totarea = np.empty(shape=[samplecount + 1])
        backward_totarea = np.empty(shape=[samplecount + 1])

        # walk forwards [0 to 1]
        # walk backwards [1 to 0]
        for i in range(0, samplecount + 1):
            forwardx = startx+(step*i)
            forwardy = self(forwardx)
            cumu_forward_totarea += forwardy
            forward_totarea[i] = cumu_forward_totarea

            backwardx = endx-(step*i)
            backwardy = self(backwardx)
            cumu_backward_totarea += backwardy
            backward_totarea[-1-i] = cumu_backward_totarea

        # no values, no bisector!
        if cumu_forward_totarea == 0:
            return None

        # set last diff to some value that will always be larger than the largest difference
        lastdiff = forward_totarea[-1]*2.0
        bisectx = None
        for i in range(samplecount + 1):
            # calculate difference for current cell
            currdiff = abs(forward_totarea[i]-backward_totarea[i])
            if currdiff == 0:
                # exact center; exit loop here
                bisectx = startx+(step*i)
                break
            if lastdiff < currdiff:
                # overshot; step back
                bisectx = startx+(step*(i-1))
                if i != 0 and lastdiff == currdiff:
                    # on the off chance that its obvious that the bisect is a mid point two samples,
                    # use the midpoint between them
                    bisectx += step*0.5
                break
            lastdiff = currdiff
        else:
            raise FuzzyError("Bisect not found. Calculation failed.")

        # return bisector
        return self(bisectx)

    def smallest_of_maximum(self, samplecount=1000):
        """Defuzzify by finding the smallest of maximum (SOM) point.

        Based on definition found on the `mathworks site`_.

        .. _mathworks site: https://www.mathworks.com/help/fuzzy/examples/defuzzification-methods.html

        Args:
            noDataHandling.NoDataSentinel: If the implication has one or more noData clipping heights that
             is not associated with a substitution value.
            samplecount (int, optional): The number of samples to take when solving the integral. Defaults to 1000.

        Returns:
            geomutils.Pt2D: The SOM point.
        """

        if self._hasNDClip:
            # assume no data substitution has already taken place.
            return NoDataSentinel(self._ignoreND)

        startx = self.minval
        endx = self.maxval
        step = (endx-startx) / samplecount

        list_of_x = []
        list_of_y = []

        for i in range(0, samplecount + 1):
            x = startx+(step*i)
            y = self(x)
            list_of_x.append(x)
            list_of_y.append(y)

        max_index = []
        max_ele = max(list_of_y)

        j = 0
        for i in list_of_y:
            if i == max_ele:
                max_index.append(j)
            j += 1

#
#        # checksum for index
#        def find_max_y_values(y_list):
#            max_value = []
#            max_ele = max(y_list)
#            for i in range(len(y_list)):
#                if list[i] == max_ele:
#                    max_value.append(y_list[i])
#            return max_value

        y_max_indexes = max_index

        # get all CurrX at max CurrY indexes

        x_at_max_y = []
        for i,x in enumerate(list_of_x):
            for j in y_max_indexes:
                if i == j:
                    x_at_max_y.append(x)

        # smallest of maximum x, y
        som_x = x_at_max_y[0]
        #som_y = max(list_of_y)

        return som_x

    def largest_of_maximum(self, samplecount=1000):
        """Defuzzify by finding the largest of maximum (LOM) point.

        Based on definition found on the `mathworks site`_.

        .. _mathworks site: https://www.mathworks.com/help/fuzzy/examples/defuzzification-methods.html

        Args:
            noDataHandling.NoDataSentinel: If the implication has one or more noData clipping heights that
             is not associated with a substitution value.
            samplecount (int, optional): The number of samples to take when solving the integral. Defaults to 1000.

        Returns:
            geomutils.Pt2D: The LOM point.
        """

        if self._hasNDClip:
            # assume no data substitution has already taken place.
            return NoDataSentinel(self._ignoreND)

        startx = self.minval
        endx = self.maxval
        step = (endx - startx) / samplecount

        list_of_x = []
        list_of_y = []

        for i in range(0, samplecount + 1):
            x = startx+(step*i)
            y = self(x)
            list_of_x.append(x)
            list_of_y.append(y)

        max_index = []
        max_ele = max(list_of_y)
        j = 0
        for i in list_of_y:
            if i == max_ele:
                max_index.append(j)
            j += 1
#
#        # checksum for index
#        def find_max_y_values(y_list):
#            max_value = []
#            max_ele = max(y_list)
#            for i in range(len(y_list)):
#                if list[i] == max_ele:
#                    max_value.append(y_list[i])
#            return max_value

        y_max_indexes = max_index

        # get all CurrX at max CurrY indexes
        x_at_max_y = []

        for i,x in enumerate(list_of_x):
            for j in y_max_indexes:
                if i == j:
                    x_at_max_y.append(x)

        # largest of maximum x, y
        lom_x = x_at_max_y[-1]
        # lom_y = max(list_of_y)

        return lom_x

    def mean_of_maximum(self, samplecount=1000):
        """Defuzzify by finding the mean/middle of maximum (MOM) point.

        Based on definition found on the `mathworks site`_.

        .. _mathworks site: https://www.mathworks.com/help/fuzzy/examples/defuzzification-methods.html

        Args:
            samplecount (int, optional): The number of samples to take when solving the integral. Defaults to 1000.

        Returns:
            noDataHandling.NoDataSentinel: If the implication has one or more noData clipping heights that
             is not associated with a substitution value.
            geomutils.Pt2D: The MOM point.
        """

        if self._hasNDClip:
            # assume no data substitution has already taken place.
            return NoDataSentinel(self._ignoreND)

        startx = self.minval
        endx = self.maxval
        step = (endx - startx) / samplecount

        list_of_x = []
        list_of_y = []

        for i in range(0, samplecount + 1):
            x = startx+(step*i)
            y = self(x)
            list_of_x.append(x)
            list_of_y.append(y)

        max_index = []
        max_ele = max(list_of_y)
        j = 0
        for i in list_of_y:
            if i == max_ele:
                max_index.append(j)
            j += 1
#
#        #checksum for index
#        def find_max_y_values(y_list):
#            max_value = []
#            max_ele = max(y_list)
#            for i in range(len(y_list)):
#                if list[i] == max_ele:
#                    max_value.append(y_list[i])
#            return max_value

        y_max_indexes = max_index

        x_at_max_y = []
        for i,x in enumerate(list_of_x):
            for j in y_max_indexes:
                if i == j:
                    x_at_max_y.append(x)

        # assuming x values are sorted, mean = (x_first+x_last)/2
        midpoint_x_at_max_y = (x_at_max_y[0]+x_at_max_y[-1])/2.

        # average of maximum x, y
        mom_x = midpoint_x_at_max_y
        # mom_y = max(list_of_y)

        return mom_x

#######################################################################


class FuzzyResult(FuzzyInput):
    """ The result portion of a rule.

    See Also:
        `FuzzyInput` class.
    """

    def get_implication(self, membname, statementclip):
        """Generate implication from result statement and supplied score.

        Args:
            membname (str): The name of the membership function to use.
            statementclip (float): The value to clip the membership function by.

        Returns:
            FuzzyImplication: Result space bounded by the upper clipping value.
        """

        curve = self.get_curve(membname)

        return FuzzyImplication(self.minval, self.maxval, [curve],
                                [statementclip if isinstance(statementclip, NoDataSentinel)
                                 else float(statementclip)])

#######################################################################


class FuzzyLogicSet(object):
    """Contains all relevant parts for constructing and evaluating Fuzzy Logic.

    Attributes:
        inputs (list): The list of input membership functions.
        result (FuzzyResult): The FuzzyResult object used to derive the implication.
        rules_string (str): String representation of all rules.
    """

    def __init__(self):
        self.inputs = []
        self.result = None
        self.rules_string = ''
        self._rules = []

    def __repr__(self):
        return 'Inputs: {0}\nRules:{1}'.format(len(self.inputs), len(self._rules))

    def import_rules(self, rules=None):
        """Import and parse individual rules.

        Each string is evaluated as seperate rule; strings that start with "#"
        are considered comments and are ignored.

        Args:
            rules (list, optional): A list of string to be evaluated as rules. If None, use rules_string attribute
              instead.

        Raises:
            FuzzyError: If there are issues with importing the rules (such as syntax errors).
        """

        self._rules = []
        if rules is None:
            rules = self.rules_string.split('\n')

        aliasdict = {}
        alstrs = []
        ifstrs = []
        currlist = None
        errs = []
        # sort statements, stripping comments and appending line breaks
        for rStr in rules:
            # remove leading whitespace
            r = rStr.strip()

            # skip blank lines and comments
            if len(r) == 0 or r[0] == '#':
                continue

            # chomp any end line comments
            comind = r.find('#')
            if comind != -1:
                r = r[:comind]

            # grab first token to see if its an 'IF' or 'DEF'
            token_1 = r.split()[0]
            if token_1.lower() == 'def':
                alstrs.append(r)
                currlist = alstrs
            elif token_1.lower() == 'if':
                ifstrs.append(r)
                currlist = ifstrs
            elif currlist is not None:
                currlist[-1] += ' '+r
            else:
                errs.append('Unbound statement: ' + r)

        # process aliases
        for i, astr in enumerate(alstrs):
            try:
                var, logic = FuzzyRule.build_alias_from_string(astr, aliasdict)
                aliasdict[var] = logic
            except FuzzyError as err:
                # if any errors occur, capture and save for reporting later.
                errs.append('DEF ' + str(i+1) + ': ' + err.message)

        # process if statements
        for i, istr in enumerate(ifstrs):
            try:
                newrule = FuzzyRule()
                newrule.build_rule_from_string(istr, aliasdict)
                self._rules.append(newrule)

            except FuzzyError as err:
                # if any errors occur, capture and save for reporting later.
                errs.append('Rule ' + str(i+1) + ': ' + err.message)

        if len(errs) > 0:
            raise FuzzyError('\n'.join(errs))

    def prepare_rule(self,rule):
        """

        :param rule:
        :param dictvals:
        :return:
        """

        rule.clear_inputs()

        for i in self.inputs:
            rule.add_input(i)
        rule.result = self.result

    def evaluate_rules(self, dictvals):
        """Use supplied values to produce a consolidated decision space.

        Args:
            dictvals (dict): A dictionary containing key-value pairs for each input.
                There should be one key matching each input, paired with an associated
                value.

        Returns:
            FuzzyImplication: Implication containing the complete decision space.

        Raises:
            FuzzyError: If No actual rules were provided.
        """

        if len(self._rules) == 0:
            raise FuzzyError("No rules to evaluate.")

        # evaluate rules individually.
        impls = []
        for r in self._rules:
            self.prepare_rule(r)
            impls.append(r.evaluate_rule(dictvals))

        # combine implications.
        tot = impls[0]
        for i in range(1, len(impls)):
            tot += impls[i]

        return tot

    @property
    def rules(self):
        """list: list of FuzzyRule objects.

        Raises:
            FuzzyError: if import_rules() has not been called.
        """
        if len(self._rules) == 0:
            raise FuzzyError("rules cannot be retrieved if 'import_rules' has not been called")
        return self._rules
