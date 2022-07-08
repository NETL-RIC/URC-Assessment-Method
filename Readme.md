## FuzzyLogic NETL-RIC Package

The **fuzzylogic** package is a tool for exploring fuzzy logic statements and response curves. 
It has been created to assist with developing Fuzzy Logic source code and application
concepts as part of **SIMPA**. This utility is compatible with both **Python 2.7.x** and **Python 3.x**.

The following python packages are required for this tool to run; any recent [Anaconda](https://www.continuum.io/)
distribution will contain all the necessary dependencies:

- [Matplotlib](http://matplotlib.org/) - Used for drawing charts.
- [Numpy](http://www.numpy.org/) - Required for Matplotlib.

To use, import the package into your existing project 

`import fuzzylogic`

## FuzzyLogic Syntax

The general fuzzy logic rule statements are declared in the form of ‘If-Then’ statements. A rule with a single input would take the form:

`IF <input1> IS <value> THEN <result> IS <value>`

Multiple membership functions can be combined using operators:

`IF <input1> IS <value> OR <input2> IS <anotherValue> THEN <result> IS <value>`

Parentheses can be used to group logical blocks together to have sub statements evaluated in a particular order:

`IF <input1> IS <value> OR (<input2> IS <anotherValue> AND <input3> IS <adiffValue>) THEN <result> IS <value>`

In the likely scenario that multiple rule statements are being declared in the “IF-THEN Rule Statements” field, each rule statement should begin on a newline. To document the rule statements, comments are supported by starting a new line with a hash/pound symbol:

`# This is a comment, and won't be processed as a rule`

_Aliases_ can be used to break down complex If-then statements, or declare a substatement that will show up repeatedly. Aliases can be thought of as _macros_ or _variables_ as defined in other languages. An alias is defined thusly:

`DEF <alias> = <compound statement>`

The alias could then be used for substituion in subsequent DEF or IF statements:
```
# either IS or = can be used for assignment
DEF <alias2> IS <alias> <...>

IF <alias> <...> THEN <...>
```

### Reserved words

All reserved words are case-insensitive, and should be space delimited.

#### Structure

- **IF** - Designates the beginning of the fuzzy rule. Must appear at the beginning of the statement.
- **THEN** - Separates the inputs clause(s) from the result clause.
- **IS** - designates the value to reference from an input or result. An equals ('=') can be used instead.
- **DEF** - Short for DEFINE; indicates a statement declaring an alias.

#### Boolean Operators

- **AND** - Selects the minimum of two input values: `<input1> IS <value1> AND <input2> IS <value2>`
- **OR** - Selects the maximum of two input values: `<input1> IS <value1> OR <input2> IS <value2>`
- **XOR** - Selects the exclusive maximum of two input values: `<input1> IS <value1> XOR <input2> IS <value2>`
- **NOT** - Inverts the value of an input: `<input> IS NOT <value>`

#### Variadic Operators

- **PRODUCT** - Multiplies two or more input values together: `PRODUCT(<input1> IS <value1>,<input2> IS <value2>,...)`
- **SUM** - Returns the result of 1 minus the product of two or more inputs: `SUM(<input1> IS <value1>,<input2> IS <value2>,...)`
- **GAMMA** - Combination of PRODUCT and SUM proportionate to gamma value. User provides a GAMMA value from 0 to 1. A GAMMA value of 0 would be equivalent to using the PRODUCT operator, while a GAMMA value of 1 would be equivalent to using the SUM operator: `GAMMA(0.6,<input1> IS <value1>,<input2> IS <value2>,...)`

#### Defuzzification methods

- **Centroid** - The areal center within the implication space; returns the x-value of the geometric centroid.
- **Bisector** - Returns the x-value of the line that vertically divides the implication space into two regions of equal area.
- **Smallest of Maximum (SOM)** - Returns the smallest x-value of all points positioned along the maximum y-value of the implication curve.
- **Middle of Maximum (MOM)** - If there is a maximum plateau in your implication, the midpoint value is returned
- **Largest of Maximum (LOM)** - If there is a maximum plateau in your implication space, the largest value is returned
