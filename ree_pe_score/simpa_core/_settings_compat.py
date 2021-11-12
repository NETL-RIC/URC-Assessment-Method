"""Module for handling backward compatibility for older version of simpa Project files."""

try:
    from .._version import __version__
except ImportError:
    from .._simpa_support_version import __version__

from .compat2or3 import dict_iteritems
import re


def _version_to_tuple(instr):
    """Get the version string as a tuple using regex.

    Version numbering scheme is a variant of semantic versioning, which is described `here <https://semver.org/>`_.

    Args:
        instr (str): The version string in "<major>.<minor>.<bugfix>b<beta> format"

    Returns:
        tuple: Version values major, minor, bugfix, beta order.

    """
    mtch = re.match(r'([0-9]+)[.]([0-9]+)[.]([0-9]+)(?:\s*b([0-9]+))?', instr)

    return (int(mtch.group(1)),
            int(mtch.group(2)),
            int(mtch.group(3)),
            int(mtch.group(4)) if mtch.group(4) is not None else 0)


def _version_less_than(lhs, rhs):
    """Strict less than ('<') for version numbers.

    Args:
        lhs (tuple): The version values for the left hand side
        rhs (tuple): The version numbers for the right hand side.

    Returns:
        bool: True if lhs < rhs; otherwise False
    """

    for i in range(4):
        if lhs[i] < rhs[i]:
            return True
        elif lhs[i] > rhs[i]:
            return False
        # else equal: continue loop

    # if we get here, the version are equal; return false
    return False

##############################
# begin migration functions


def _migrate_0_2_0_1(insettings):
    """Migrate to 0.2.0b1 from any previous version.

    Args:
        insettings (dict): The dictionary representation of the saved json settings.


    """

    def _update_defuzz(instr):
        if instr == 'smallestOfMaximum':
            return 'smallest_of_maximum'
        if instr == 'meanOfMaximum':
            return 'mean_of_maximum'
        if instr == 'largestOfMaximum':
            return 'largest_of_maximum'
        return instr

    inpfiles = insettings.get('inputFiles', [])

    for inp in inpfiles:
        if 'maxval' not in inp:
            inp['maxval'] = inp.get('maxVal', 1.0)
        if 'minval' not in inp:
            inp['minval'] = inp.get('minVal', 0.0)

    for _, fls in dict_iteritems(insettings['fuzzyLogicSets']):
        if 'maxval' not in fls['result']:
            fls['result']['maxval'] = fls['result'].get('maxVal', 1.0)
        if 'minval' not in fls['result']:
            fls['result']['minval'] = fls['result'].get('minVal', 0.0)

        if 'rules_string' not in fls:
            fls['rules_string'] = fls.get('rulesStr', '')

        for inp in fls['inputs']:
            if 'maxval' not in inp:
                inp['maxval'] = inp.get('maxVal', 1.0)
            if 'minval' not in inp:
                inp['minval'] = inp.get('minVal', 0.0)

    for _, co in dict_iteritems(insettings['fuzzyLogicCombiners']):
        co['defaultDefuzzOperator'] = _update_defuzz(co['defaultDefuzzOperator'])

        defops = co.get('defuzzOperators', None)
        if defops:
            for k in list(defops.keys()):
                defops[k] = _update_defuzz(defops[k])


##############################
# end migration functions


def _do_compat_updates(insettings, s_version):
    """Do actual compatibility updates based on s_version.

    Args:
        insettings (dict): The dictionary representation of the saved json settings.
        s_version (tuple): Values composing the semantic version number of the values in insettings.

    Returns:
        bool: `true` if migration occurs; `false` otherwise.

    See Also:
        _version_to_tuple()
    """

    migrated = False

    # versions where format updated
    #                <version tuple>, <migration func>
    version_list = [((0, 2, 0, 1),    _migrate_0_2_0_1)]
    # add more as needed...

    for vf in version_list:
        trg_vers = vf[0]
        migrate = vf[1]
        if _version_less_than(s_version, trg_vers):
            migrate(insettings)
            migrated = True
    return migrated


# cache version value for SIMPA
_simpa_version = _version_to_tuple(__version__)


def compat_check(insettings):
    """Check to see if the input data needs to be updated. If so, update to current version.

    Args:
        insettings (dict): The dictionary representation of the saved json settings.

    Returns:
        bool: `true` if insettings required an update and was updated; `false` otherwise.
    """

    test_version = _version_to_tuple(insettings.get('version', '0.0.0b0'))

    return _do_compat_updates(insettings, test_version)
