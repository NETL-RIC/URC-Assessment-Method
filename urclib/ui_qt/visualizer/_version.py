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

