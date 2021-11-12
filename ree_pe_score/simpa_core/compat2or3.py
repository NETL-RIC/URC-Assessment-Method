"""Module for simplifying issues with maintaining compatibility with both python 2.x and 3.x.

The following imports are overloaded:
    * ABC (Abstract base class)
    * builtins

The following methods are implemented differently for python 2.x and 3.x:
    * isstring(s) - Check if variable s is a string.
    * dict_iteritems(d) - return an iterable object for moving over all items in d.
    * c_input(s) - Read input from the console / CLI, using s as the prompt.

"""

# makes some stuff in python 2 act like python 3
from __future__ import absolute_import, division, print_function, unicode_literals

import sys

# function hooks
isstring = None
dict_iteritems = None
c_input = None

if sys.version_info[0] != 3:
    # python 2

    from abc import ABCMeta

    # Trick from:
    # https://stackoverflow.com/questions/35673474/using-abc-abcmeta-in-a-way-it-is-compatible-both-with-python-2-7-and-python-3-5
    ABC = ABCMeta(str('ABC'), (object,), {'__slots__': ()})

    import __builtin__ as builtins
    from sets import Set as set

    def _isstring2(s): return isinstance(s, basestring)

    def _dict_iteritems2(d): return d.iteritems()


    def _compatfilter2(*args, **kwargs): return iter(filter(*args, **kwargs))

    isstring = _isstring2
    dict_iteritems = _dict_iteritems2
    c_input = raw_input
    iter_filter = _compatfilter2
else:
    # python 3

    from abc import ABC
    import builtins


    def _isstring3(s): return isinstance(s, str)

    def _dict_iteritems3(d): return d.items()

    def _compatfilter3(*args, **kwargs): return filter(*args, **kwargs)

    isstring = _isstring3
    dict_iteritems = _dict_iteritems3
    c_input = input

    iter_filter = _compatfilter3
