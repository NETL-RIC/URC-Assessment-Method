"""Version related information for compatibility checks.
Uses semantic versioning.

"""

# add comment tags below to make it easier to locate and auto increment version numbers

# version numbers
VERS_MAJOR = 0
VERS_MINOR = 8
VERS_FIX = 0
# /version numbers

VERSION = (VERS_MAJOR,VERS_MINOR,VERS_FIX)

def check_version(major,minor=None,fix=None):
    """Compare version numbers to see if valid.

    Args:
        major (int): The major version number to compare.
        minor (int,optional): The minor version number to compare. Ignored if `None`.
        fix (int,optional): The fix number to compare. Ignored if `None` or `minor` is `None`.

    Returns:
        int: One of the following:
         * -1 if inbuilt version is less than provided version.
         * 0 if the provided version numbers are equal.
         * 1 if inbuilt version is greater than provided version.
    """
    for lhs,rhs in zip(VERSION,(major,minor,fix)):
        if rhs is None:
            break
        if lhs<rhs:
            return -1
        elif lhs>rhs:
            return 1

    return 0

