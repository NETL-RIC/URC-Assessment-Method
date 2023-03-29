# This file is part of URC Assessment Method.
#
# URC Assessment Method is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# URC Assessment Method is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with URC Assessment Method. If not, see
# <https://www.gnu.org/licenses/>.

"""Classes for loading and saving FuzzyLogic classes to JSON files.

Authors:
  * Patrick Wingo

Version: 0.1

"""

from __future__ import absolute_import, division, print_function, unicode_literals

from . import fuzzylogic as fl
from . import fuzzycurves as fc
from . import geomutils as gu

import json


class FLEncoder(json.JSONEncoder):
    """Class for encoding GeomUtils and FuzzyLogic types."""
    
    def default(self, o):
        """`json.JSONEncoder`_ overload.

        Args:
            o (object): See `json.JSONEncoder`_ documentation.

        Returns:
            `object`: See `json.JSONEncoder`_ documentation.

        .. _json.JSONEncoder: https://docs.python.org/3/library/json.html#json.JSONEncoder
        """
        
        # geom utils
        if type(o) == gu.Pt2D:
            return FLEncoder._serialize_pt2d(o)
        if isinstance(o, gu.BaseSegment):
            return FLEncoder._serialize_segment(o)
            
        # fuzzy logic
        if type(o) == fl.FuzzyValue:
            return FLEncoder._serialize_fuzzyvalue(o)
        if isinstance(o, fc.FuzzyCurve):
            return FLEncoder._serialize_template_curve(o)
        if type(o) == fl.FuzzyRule:
            return FLEncoder._serialize_fuzzyrule(o)
        if isinstance(o, fl.FuzzyInput):
            return FLEncoder._serialize_fuzzyinput(o)
        if type(o) == fl.FuzzyImplication:
            return FLEncoder._serialize_fuzzyimplication(o)
        elif type(o) == fl.FuzzyLogicSet:
            return FLEncoder._serialize_fuzzylogicset(o)
            
        return json.JSONEncoder.default(self, o)
        
    @staticmethod
    def _serialize_pt2d(o):
        """Serialize Pt2D objects.

        Args:
            o (components.fuzzylogic.geomutils.Pt2D): The Pt2D object to serialize.
        
        Returns:
            `dict`: Objects to be encoded as JSON.
        """
        return {'pyType': 'Pt2D', 'x': o.x, 'y': o.y}
        
    @staticmethod
    def _serialize_segment(o):
        """Serialize BaseSegment-subclass objects.

        Args:
            o (components.fuzzylogic.geomutils.BaseSegments): The BaseSegment-subclass object to serialize.

        Returns:
            `dict`: Objects to be encoded as JSON.
        """
        
        return {'pyType': type(o).__name__,
                'p1': FLEncoder._serialize_pt2d(o.lowPoint),
                'p2': FLEncoder._serialize_pt2d(o.highPoint),
                'values': o.equation_args}
    
    # fuzzy logic
    @staticmethod
    def _serialize_fuzzyvalue(o):
        """Serialize FuzzyValue objects.

        Args:
            o (components.fuzzylogic.fuzzylogic.FuzzyValue): The FuzzyValue object to serialize.

        Returns:
            `dict`: Objects to be encoded as JSON.
        """
        
        if o is None:
            return None
        return {'pyType': 'FuzzyValue', 'tStat': o._tStat, 'truthValue': o.truthValue}
    
    @staticmethod
    def _serialize_piecewise_curve(o):
        """Serialize FuzzyCurve objects.

        Args:
            o (components.fuzzylogic.fuzzyCurves.PiecewiseCurve): The PiecewiseCurve object to serialize.

        Returns:
            `dict`: Objects to be encoded as JSON.
        """
        
        if o is None:
            return None
        ret = {'pyType': type(o).__name__, 'name': o.name, 'segments': [FLEncoder._serialize_segment(s)
                                                                        for s in o._segments]}
        return ret

    @staticmethod
    def _serialize_template_curve(o):
        """Serialize FuzzyCurve objects.

        Args:
            o (components.fuzzylogic.fuzzyCurves.FuzzyCurve): The FuzzyCurve subclass object to serialize.

        Returns:
            `dict`: Objects to be encoded as JSON.
        """

        if o is None:
            return None

        if type(o).__name__ == 'PiecewiseCurve':
            return FLEncoder._serialize_piecewise_curve(o)

        ret = {'pyType': type(o).__name__, 'name': o.name}

        allprops = fc.get_propdetails_for_obj(o)

        for e in allprops:
            ret[e.prop] = getattr(o, e.prop)

        return ret

    @staticmethod
    def _serialize_fuzzyrule(o):
        """Serialize FuzzyRule objects.

        Args:
            o (components.fuzzylogic.fuzzylogic.FuzzyRule): The FuzzyRule object to serialize.

        Returns:
            `dict`: Objects to be encoded as JSON.
        """
        
        if o is None:
            return None
        ret = {'pyType': 'FuzzyRule', 'inputs': [FLEncoder._serialize_fuzzyinput(o._inputs[k])
                                                 for k in o._inputs.keys()],
               'result': FLEncoder._serialize_fuzzyinput(o.result)}
        # skip execStatement since it should be recompiled before run anyway.
        
        return ret
        
    @staticmethod
    def _serialize_fuzzyinput(o):
        """Serialize FuzzyInput objects.

        Args:
            o (components.fuzzylogic.fuzzylogic.FuzzyInput): The FuzzyInput object to serialize.

        Returns:
            `dict`: Objects to be encoded as JSON.
        """
    
        if o is None:
            return None
        ret = {'pyType': type(o).__name__, 'name': o.name, 'minval': o.minval, 'maxval': o.maxval,
               'truthCurves': [FLEncoder._serialize_template_curve(o._truthCurves[k]) for k in o._truthCurves.keys()]}
        return ret
        
    @staticmethod
    def _serialize_fuzzyimplication(o):
        """Serialize FuzzyImplication objects.

        Args:
            o (components.fuzzylogic.fuzzylogic.FuzzyImplication): The FuzzyImplication object to serialize.

        Returns:
            `dict`: Objects to be encoded as JSON.
        """
        
        if o is None:
            return None
        return {'pyType': 'FuzzyImplication', 'curve': FLEncoder._serialize_template_curve(o._curve),
                'minval': o.minval, 'maxval': o.maxval}
                
    @staticmethod
    def _serialize_fuzzylogicset(o):
        """Serialize FuzzyLogicSet objects.

        Args:
            o (components.fuzzylogic.fuzzylogic.FuzzyLogicSet): The FuzzyLogicSet object to serialize.

        Returns:
            `dict`: Objects to be encoded as JSON.
        """
        
        if o is None:
            return None
        ret = {'pyType': 'FuzzyLogicSet', 'result': FLEncoder._serialize_fuzzyinput(o.result),
               'inputs': [FLEncoder._serialize_fuzzyinput(x) for x in o.inputs],
               'rules': [FLEncoder._serialize_fuzzyrule(x) for x in o._rules], 'rules_string': o.rules_string}
        return ret
        
#######################################################################
# decoding stuff


class FLDecoder(json.JSONDecoder):
    """Class for decoding GeomUtils and FuzzyLogic types.

    Args:
        *args: Variable-length arguments passed to the parent constructor.
        **kwargs: Keyword arguments passed to the parent constructor.
    """
    
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    @staticmethod
    def _dict_to_pt2d(d):
        """Decode a Pt2D object from a dictonary.

        Args:
            d (dict): Description of the Pt2D object.

        Returns:
            components.fuzzylogic.geomutils.Pt2D: A newly constructed Pt2D object, or None if d is None.
        """
        if d is None:
            return None
        return gu.Pt2D(d['x'], d['y'])

    @staticmethod
    def _dict_to_segment(d):
        """Decode a BaseSegment-subclass object from a dictonary.

        Args:
            d (dict): Description of the BaseSegment-subclass object.

        Returns:
            components.fuzzylogic.geomutils.BaseSegment: A newly constructed BaseSegment-subclass object, or
              None if d is None.
        """

        if d is None:
            return None
        thetype = getattr(gu, d['pyType'])
        
        ret = thetype(d['p1'], d['p2'])
        ret.equation_args = d['values']
        return ret

    @staticmethod
    def _dict_to_fuzzyvalue(d):
        """Decode a FuzzyValue object from a dictonary.

        Args:
            d (dict): Description of the FuzzyValue object.

        Returns:
            components.fuzzylogic.fuzzylogic.FuzzyValue: A newly constructed FuzzyValue object, or None if d is None.
        """

        if d is None:
            return None
        return fl.FuzzyValue(d['tStat'], d['truthValue'])
                
    @staticmethod
    def _dict_to_piecewise_curve(d):
        """Decode a PiecewiseCurve object from a dictonary.

        Args:
            d (dict): Description of the FuzzyCurve object.

        Returns:
            components.fuzzylogic.fuzzylogic.PiecewiseCurve: A newly constructed FuzzyCurve object, or None if d is
            None.
        """
        
        if d is None:
            return None
        seglist = d['segments']
        return fc.PiecewiseCurve(d['name'], seglist)

    @staticmethod
    def _dict_to_template_curve(tstr, d):
        """Decode a FuzzyCurve object from a dictonary.

        Args:
            d (dict): Description of the FuzzyCurve object.

        Returns:
            components.fuzzylogic.fuzzylogic.FuzzyCurve: A newly constructed FuzzyCurve subclass object,
            or None if d is None.
        """

        if d is None:
            return None

        # construct the proper curve
        thetype = getattr(fc, d['pyType'])
        curve = thetype(d['name'])
        if curve is None:
            raise fc.FuzzyError('Undefined curve type: '+tstr)

        # find attributes to retrieve, and assign
        allprops = fc.get_propdetails_for_obj(curve)

        for e in allprops:
            setattr(curve, e.prop, d[e.prop])

        return curve

    @staticmethod
    def _dict_to_fuzzyrule(d):
        """Decode a FuzzyRule object from a dictonary.

        Args:
            d (dict): Description of the FuzzyRule object.

        Returns:
            components.fuzzylogic.fuzzylogic.FuzzyRule: A newly constructed FuzzyRule object, or None if d is None.
        """

        if d is None:
            return None
        ret = fl.FuzzyRule()
        for i in d['inputs']:
            ret.add_input(i)
        if 'result' in d:
            ret.result = d['result']
        else:
            # for legacy compatibility
            for r in d['results']:
                ret.result = r
                break
        
        return ret
                
    @staticmethod
    def _dict_to_fuzzyinput(d):
        """Decode a FuzzyInput object from a dictonary.

        Args:
            d (dict): Description of the FuzzyInput object.

        Returns:
            components.fuzzylogic.fuzzylogic.FuzzyInput: A newly constructed FuzzyInput object, or None if d is None.
        """

        if d is None:
            return None
        thetype = getattr(fl, d['pyType'])
        ret = thetype(d['name'], d['minval'], d['maxval'])
        for tc in d['truthCurves']:
            ret.add_curve(tc)
        
        return ret
                
    @staticmethod
    def _dict_to_fuzzyimplication(d):
        """Decode a FuzzyImplication object from a dictonary.

        Args:
            d (dict): Description of the FuzzyImplication object.

        Returns:
            components.fuzzylogic.fuzzylogic.FuzzyImplication: A newly constructed FuzzyImplication object, or
              None if d is None.
        """

        if d is None:
            return None
        return fl.FuzzyImplication(d['minval'], d['maxval'], d['curve'])
                
    @staticmethod
    def _dict_to_fuzzylogicset(d):
        """Decode a FuzzyLogicSet object from a dictonary.

        Args:
            d (dict): Description of the FuzzyLogicSet object.

        Returns:
            components.fuzzylogic.fuzzylogic.FuzzyLogicSet: A newly constructed FuzzyLogicSet object, or
              None if d is None.
        """

        if d is None:
            return None
        ret = fl.FuzzyLogicSet()
        ret.result = d['result']
        ret.inputs = d['inputs']
        ret._rules = d['rules']
        ret.rules_string = d['rules_string']

        if 'rounding' in d:
            gu.prec = 10 ** -d['rounding']
        return ret
            
    def object_hook(self, indict):
        """`json.JSONDecoder`_ overload.

        Args:
            indict (dict): See `json.JSONDecoder`_ documentation.

        Returns:
            object: See `json.JSONDecoder`_ documentation.

        .. _json.JSONDecoder: https://docs.python.org/3/library/json.html#json.JSONDecoder
        """
        
        if 'pyType' in indict:
            typestr = indict['pyType']
            
            inputtypes = ['FuzzyInput', 'FuzzyResult']
            segtypes = gu.segment_types()
            if typestr == 'Pt2D':
                return FLDecoder._dict_to_pt2d(indict)
            if typestr in segtypes:
                return FLDecoder._dict_to_segment(indict)
            if typestr == 'FuzzyValue':
                return FLDecoder._dict_to_fuzzyvalue(indict)
            if typestr == 'FuzzyCurve' or typestr == 'PiecewiseCurve':
                return FLDecoder._dict_to_piecewise_curve(indict)
            if typestr in fc.get_curve_typenames():
                return FLDecoder._dict_to_template_curve(typestr, indict)
            if typestr == 'FuzzyRule':
                return FLDecoder._dict_to_fuzzyrule(indict)
            if typestr in inputtypes:
                return FLDecoder._dict_to_fuzzyinput(indict)
            if typestr == 'FuzzyImplication':
                return FLDecoder._dict_to_fuzzyimplication(indict)
            if typestr == 'FuzzyLogicSet':
                return FLDecoder._dict_to_fuzzylogicset(indict)
        
        # default
        return indict
    
#######################################################################
# Exposed Methods


def save_settings(fset, path):
    """Save a FuzzyLogicSet object to disk.

    Args:
        fset (components.fuzzylogic.fuzzylogic.FuzzyLogicSet): The FuzzyLogicSet object to save.
        path (str): Path to the file to write.
    """
    with open(path, 'w') as outFile:
        json.dump(fset, outFile, cls=FLEncoder)
    
    
def load_settings(path):
    """Load a FuzzyLogicSet object from disk.

    Args:
        path (str): Path to the file to load.

    Returns:
        components.fuzzylogic.fuzzylogic.FuzzyLogicSet: A FuzzyLogicSet object populated with the contents of the file.
    """
    with open(path, 'r') as inFile:
        return json.load(inFile, cls=FLDecoder)
