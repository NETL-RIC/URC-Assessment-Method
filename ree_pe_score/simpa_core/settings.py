"""Module for managing SIMPA simulation parameters."""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os

import numpy as np

from .drawutils import SimpaColor
try:
    from .._version import __version__
except ImportError:
    from .._simpa_support_version import __version__
from .compat2or3 import *
from .containers import serialize_combiner, deserialize_combiner
from ..fuzzylogic import FuzzyError
from ..fuzzylogic.settings import FLEncoder, FLDecoder
from ._settings_compat import compat_check

class Settings(object):
    """Container for storing SIMPA settings.
    
Attributes:
    dataInputs (list): A list of dicts detailing the data inputs for the simulation.
    flSets (dict): A name-value set of FuzzyLogicSets objects.
    flCombiners (dict): A name-value set of FLCombiners.
    inputDir (str): The directory used for searching input values.
    outputDir (str): The directory for writing output values.
    noVal (float): The value to represent no data.
    settingsPath (str): Path to the file storing the present settings; can be None if no file exists.
    """

    def __init__(self):

        self.clear()

    def clear(self):
        """Reset to default values.
        """
        self.dataInputs = []
        self.flSets = {}
        self.flCombiners = {}
        self.inputDir = None
        self.outputDir = None
        self.noVal = -999999.
        self.ndMethod = 'ignore'
        self.ndSubVal = 0.0

        # not populated from json
        self.settingsPath = ''

    def get_absinputdir(self):
        """Get the absolute path to the input directory.

        Resolves any relative paths as being relative to the settingsPath attribute. If no project file is loaded, then
        any relative path will be resolved as being relative to the current working directory.

        Returns:
          `str`: The absolute representation of the inputDir attribute.
        """

        return self._get_abspath(self.inputDir)

    def get_absoutputdir(self):
        """Get the absolute path to the output directory.

        Resolves any relative paths as being relative to the settingsPath attribute. If no project file is loaded, then
        any relative path will be resolved as being relative to the current working directory.

        Returns:
            `str`: The absolute representation of the outputDir attribute.
        """

        return self._get_abspath(self.outputDir)

    def validate(self):
        """Check to see if all input fields are valid for a simulation run.

        Returns:
            `tuple`: With the following fields:
              0. `bool`: True if valid; False otherwise.
              1. `list`: Zero or more strs describing any errors encountered.
        """
        errlist = []

        # check to see if output is defined.
        if self.outputDir is None or len(self.outputDir) == 0:
            errlist.append('No output directory defined.')

        # check to see if all fl inputs map to a named input
        inpnames = [d['fieldName'] for d in self.dataInputs]
        for k, v in dict_iteritems(self.flSets):
            for i in v.inputs:
                if i.name not in inpnames:
                    errlist.append('Input "' + i.name + '" in Fuzzy Logic Set "' + k + '" does not match any file'
                                                                                       'input labels')
            # check to see fl statements are valid
            try:
                v.import_rules()
            except FuzzyError as err:
                errlist.append('Syntax error encountered in Fuzzy Logic Set "' + k + '":' + err.message)

        # check to see if all combiner variables map to a set
        flsnames = list(self.flSets.keys())
        for k, v in dict_iteritems(self.flCombiners):

            imps = v.found_implication_names
            if len(imps) > 0:
                for i in imps:
                    if i not in flsnames:
                        errlist.append('Reference "' + i + '" in Result Rule "' + k +
                                       '" does not match any fuzzy logic sets')
            else:
                errlist.append('Result Rule "' + k +
                               '" must not be empty')
            # todo: check to see if Combiner statements are valid

        return len(errlist) == 0, errlist

    def write_summary_to_outdir(self):
        """Write summary to 'Parameter Summary.txt' in output directory"""

        self.summary_to_file(self._get_abspath(self.outputDir) + '/Parameter Summary.txt')

    def summary_to_file(self, filepath):
        """ Write a summary of all current settings

        Args:
            filepath (str): Path to write summary to.

        """

        with open(filepath, 'w') as outFile:
            indent = '    '
            ilvl = 0

            # begin closures for formatting
            def _whitespace():
                print('', file=outFile)

            def _header(txt):
                _whitespace()
                print((indent * ilvl) + txt, file=outFile)
                print((indent * ilvl) + '~' * len(txt), file=outFile)

            def _subheader(txt):
                print((indent * ilvl) + txt + ':', file=outFile)

            def _param_val(lbl, val):
                print((indent * ilvl) + lbl + ': ' + str(val), file=outFile)

            def _block_val(lbl, valstr):

                print((indent * ilvl) + lbl + ':', file=outFile)
                sublvl = ilvl + 1
                lines = valstr.split('\n')
                for ln in lines:
                    ln = ln.strip()
                    if len(ln) > 0:
                        print((indent * sublvl) + ln, file=outFile)

            # end closures
            ###########
            _header('Inputs')
            ilvl += 1
            for di in self.dataInputs:
                _param_val(di['fieldName'], di['baseName'])
            ilvl -= 1

            ###########
            _header('Fuzzy Logic Rule Sets')
            ilvl += 1
            for k, v in dict_iteritems(self.flSets):
                _subheader(k)
                ilvl += 1
                _subheader('Inputs')
                ilvl += 1
                for inp in v.inputs:
                    _subheader(inp.name)
                    ilvl += 1
                    _param_val('Range', '[' + str(inp.minval) + ', ' + str(inp.maxval) + ']')
                    _param_val('Values', ', '.join([n for n, _ in dict_iteritems(inp._truthCurves)]))
                    ilvl -= 1
                ilvl -= 1
                _subheader('Result')
                ilvl += 1
                _param_val('Range', '[' + str(v.result.minval) + ', ' + str(v.result.maxval) + ']')
                _param_val('Values', ', '.join([n for n, _ in dict_iteritems(v.result._truthCurves)]))
                ilvl -= 1

                _block_val('Rules', v.rules_string)
                ilvl -= 1
                _whitespace()
            ilvl -= 1

            ###########
            _header('Combining Expressions')
            ilvl += 1
            for k, v in dict_iteritems(self.flCombiners):
                _subheader(k)
                ilvl += 1
                _block_val('Combining Expression', v._comboLogic)
                _subheader('Defuzzifiers')
                ilvl += 1
                _param_val('Default', v._defaultDefuzz)
                _whitespace()
                for dk, dv in dict_iteritems(v._defuzzOps):
                    _param_val(dk, dv)
                ilvl -= 1
                ilvl -= 1
                _whitespace()

            ilvl -= 1

            ###########
            _header('Other Settings')
            ilvl += 1
            ndstr = self.ndMethod
            if ndstr == 'substitute':
                ndstr += ' (' + str(self.ndSubVal) + ')'
            _param_val('No Data Treatment', ndstr)
            _param_val('Output Directory', self.outputDir)
            _param_val('No Data Value for output', self.noVal)

            ilvl -= 1

    def _get_abspath(self, thepath):
        """

        Args:
            thepath (str): Path to get an absolute representation of.

        Resolves any relative paths as being relative to the settingsPath attribute. If no project file is loaded, then
        any relative path will be resolved as being relative to the current working directory.

        Returns:
            `str`: The absolute representation of the thePath argument.

        """

        if thepath is not None and os.path.isabs(thepath):
            return thepath

        base = os.path.abspath(os.path.curdir)
        if self.settingsPath is not None:
            base = os.path.abspath(self.settingsPath)
            if not os.path.isdir(base):
                base = os.path.dirname(base)

        base += os.path.sep

        if thepath is not None:
            base += thepath + os.path.sep

        return base

    def purge_preloaded(self):
        """Purges any preloaded raster references from `dataInputs`. This is needed for parallel running,
        as gdal.Datasets are not pickeable. Since preloaded is intended for SIMPA running as part of a larger
        service, this should not destroy data.
        """

        for di in self.dataInputs:
            if 'preloaded' in di:
                di['preloaded']=None

#####


def load_settings(filepath):
    """Load settings from an existing input file.

    Args:
        filepath (str): Path to the file to load.

    Returns:
        Settings: A new Settings object initialized with data from the file at filePath.
    """

    ret = Settings()
    with open(filepath, 'r') as inFile:
        json_str = inFile.read()

        # begin compat section
        # load json in to plain old data types
        tocheck = json.loads(json_str)
        if compat_check(tocheck):
            # re-encode if need be.
            json_str = json.dumps(tocheck)
        # end compat section

        ret = json.loads(json_str, cls=_SettingsDecoder)

        # make sure everything is up to date
        ret.settingsPath = os.path.abspath(filepath)
        for di in ret.dataInputs:
            di['_expandedBase'] = os.path.normpath(os.path.join(os.path.dirname(ret.settingsPath), di['baseName']))
    return ret


def save_settings(thesettings, filepath):
    """Save the settings to a file.

    Args:
        thesettings (Settings): Values to write to a file.
        filepath (str): Path to the file to write.

    """
    content = json.dumps(thesettings, cls=_SettingsEncoder)

    with open(filepath, 'w') as outFile:
        # do the safe thing and dump to string first;
        # if that succeeds, then write to file
        outFile.write(content)
        thesettings.settingsPath = os.path.abspath(filepath)


#####################################################################################################################
class _SettingsEncoder(json.JSONEncoder):
    """Subclass for encoding Settings objects in a way that is serializable using JSON.
    """

    def default(self, o):
        """`json.JSONEncoder`_ overload.

        Args:
            o (object): See `json.JSONEncoder`_ documentation.

        Returns:
            `object`: See `json.JSONEncoder`_ documentation.

        .. _json.JSONEncoder: https://docs.python.org/3/library/json.html#json.JSONEncoder

        """
        if type(o) == Settings:

            retdict = {'pyType': 'simpaSettings',
                       'version': __version__,
                       'inputDirectory': o.inputDir,
                       'outputDirectory': o.outputDir,
                       'inputFiles': self.__class__.scrub_dictlist(o.dataInputs),
                       'noVal': o.noVal,
                       'noDataMethod': o.ndMethod,
                       'noDataSubValue': o.ndSubVal}

            flsencoder = FLEncoder()
            flsdata = {}
            for k, v in dict_iteritems(o.flSets):
                flsdata[k] = flsencoder.default(v)
            retdict['fuzzyLogicSets'] = flsdata

            flcdata = {}
            for k, v in dict_iteritems(o.flCombiners):
                flcdata[k] = serialize_combiner(v)
            retdict['fuzzyLogicCombiners'] = flcdata
            return retdict

        if type(o) == SimpaColor:
            return {'r': o.r,
                    'g': o.g,
                    'b': o.b,
                    'a': o.a,
                    'pyType': 'SimpaColor'}
        if type(o) == np.float32:
            return float(o)
        if type(o) == np.int32:
            return int(o)

        return json.JSONEncoder.default(self, o)

    @staticmethod
    def scrub_dictlist(list_toscrub):
        """Remove any entries from dictionaries whose keys start with an underscore (_).

        Args:
            list_toscrub (list): List of dictionaries to check.

        Returns:
            A list with the content of listToScrub, but with each underscored key removed from each dictionary.
        """
        return [{k: v for k, v in dict_iteritems(d) if k[0] != '_'} for d in list_toscrub]


#####################################################################################################################
class _SettingsDecoder(json.JSONDecoder):
    """Subclass for decoding serializable objects originating from JSON into a Settings object.

    Args:
        *args: Variable-length arguments passed to the parent constructor.
        **kwargs: Keyword arguments passed to the parent constructor.
    """

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, indict):
        """`json.JSONDecoder`_ overload.

        Args:
            indict (dict): See `json.JSONDecoder`_ documentation.

        Returns:
            object: See `json.JSONDecoder`_ documentation.

        .. _json.JSONDecoder: https://docs.python.org/3/library/json.html#json.JSONDecoder
        """
        fldecoder = FLDecoder()
        # assume entry is settings record
        if 'pyType' in indict:

            if indict['pyType'] == 'simpaSettings':
                ret = Settings()

                ret.inputDir = indict['inputDirectory']
                ret.outputDir = indict['outputDirectory']
                ret.dataInputs = indict['inputFiles']
                ret.noVal = indict['noVal']
                ret.ndMethod = indict.get('noDataMethod', 'ignore')
                ret.ndSubVal = indict.get('noDataSubValue', 0.0)
                ret.flSets = indict['fuzzyLogicSets']
                ret.flCombiners = indict['fuzzyLogicCombiners']
                return ret

            elif indict['pyType'] == 'FLCombiner':
                return deserialize_combiner(indict)
            elif indict['pyType'] == 'SimpaColor':
                return SimpaColor(indict['r'], indict['g'], indict['b'], indict['a'])
            else:
                return fldecoder.object_hook(indict)

        return indict
