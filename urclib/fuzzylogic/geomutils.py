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

"""Simple geometry functions and methods

Author: Patrick Wingo

Version: 0.1

External Dependencies:
    * `numpy <https://www.numpy.org/>`_

"""

from __future__ import absolute_import, division, print_function, unicode_literals
from abc import abstractmethod
from math import exp
import numpy as np

import sys

if sys.version_info[0] != 3:
    from abc import ABCMeta

    # Trick from:
    # https://stackoverflow.com/questions/35673474/using-abc-abcmeta-in-a-way-it-is-compatible-both-with-python-2-7-and-python-3-5
    ABC = ABCMeta(str('ABC'), (object,), {'__slots__': ()})
else:
    from abc import ABC

##############################################
# Utility


def bounds_check(inval, lo=0.0, hi=1.0, eps=1e-6):
    """Check that a value is between boundaries, allowing for a small amount of drift or error.

    Args:
        inval (float): The value to test.
        lo (float, optional): The lower boundary; defaults to 0.0.
        hi (float, optional): The upper boundary; defaults to 1.0.
        eps (float,optional): The epsilon value, which determines how much drift is tolerated; defaults to 1e-6.

    Returns:
        float: The value of `inval` if it falls between `lo` and `hi`, or the nearest boundary value if `inval` is
          within the tolerance value `eps`.
        None: If `inval` is out of bounds.

    Raises:
        ValueError: If `inval` out of bounds and outside the tolerance range.

    """

    if inval >= lo and inval <= hi:
        return inval
    if inval < lo:
        if lo - inval < eps:
            return lo
    if inval > hi:
        if inval - hi < eps:
            return hi

    raise ValueError('inval must be in the range of [{0},{1}]', 'Value is {2}'.format(lo, hi, inval))


def get_segmentlabelmappings():
    """Retrieve a list of mappings of segment types and their display labels.

    Returns:
        list: tuples with the following values:
          0. `str`: The name of the segment class.
          1. `str`: The display name of the segment type.
    """
    return [(LinearSegment.__name__, 'Linear Segment'),
            (StepwiseSegment.__name__, 'Stepwise Segment'),
            (BezierSegment.__name__, 'Smooth Curve segment')]


def segment_types():
    """Report the list of classnames for segment types defined in this module.
    
Returns:
    list: Names of BaseSegment-subclasses ready to be used.
    """
    return [s[0] for s in get_segmentlabelmappings()]


def pretty_segment_names():
    """Report the list of display-ready segment names in this module.

    Returns:
        list: Display Names of segment types defined in this module.
    """
    return [s[1] for s in get_segmentlabelmappings()]


def pretty_segment_to_type(lbl):
    """Retrieve the class name for a segment based on a display-ready dlg_label.

    Args:
        lbl (str): The dlg_label to query.

    Returns:
        * str: The class name that is mapped to the value in lbl.
        * None: If lbl does not match any class names.
    """
    for n, p in get_segmentlabelmappings():
        if lbl == p:
            return n

    # not found
    return None


def type_segment_to_pretty(lbl):
    """Retrieve the display-ready dlg_label based on a segment class name.

    Args:
        lbl (str): The class name to query.

    Returns:
        * str: The pretty dlg_label that is mapped to the value in lbl.
        * None: If lbl does not match any pretty labels.
    """

    for n, p in get_segmentlabelmappings():
        if lbl == n:
            return p

    # not found
    return None


##############################################

class Pt2D(object):
    """Straightforward 2D point class.

    Args:
        x (float, optional): The initial x-coordinate. Defaults to 0.
        y (float, optional): The initial y-coordinate. Defaults to 0.
    """

    def __init__(self, x=0, y=0):

        # reserve names for operators
        self._x = None
        self._y = None
        self.x = x
        self.y = y

    def __eq__(self, rhs):
        if rhs is None:
            return False

        return np.allclose([self._x, self.y], [rhs._x, rhs._y])

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __getitem__(self, ind):
        """Index operator overload.
        
        Args:
            ind (int or str): Reference to the coordinate to retrieve.

        Returns:
            float: The value of the request coordinate.

        Raises:
            IndexError: If ind is not a coordinate name or a valid index.
        """

        outval = None
        if ind == 0 or ind == 'x' or ind == 'X':
            outval = self._x
        elif ind == 1 or ind == 'y' or ind == 'Y':
            outval = self._y
        else:
            raise IndexError("Index out of bounds; must be 0, 1, 'x', or 'y'")

        return outval

    def __setitem__(self, ind, val):
        """Index operator overload.
        
        Args:
            ind (int or str): The reference to the coordinate to assign.
            val (float): The value to assign.

        Raises:
            IndexError: If ind is not a coordinate name or a valid index.
        """

        # Use properties to ensure any conversions take place.
        outval = None
        if ind == 0 or ind == 'x' or ind == 'X':
            self.x = val
        elif ind == 1 or ind == 'y' or ind == 'Y':
            self.y = val
        else:
            raise IndexError("Index out of bounds; must be 0, 1, 'x', or 'y'")

        return outval

    def __repr__(self):
        return '({0},{1})'.format(self._x, self._y)

    def __str__(self):
        return '({0},{1})'.format(float(self._x), float(self._y))

    def __add__(self, p2):
        if isinstance(p2, Pt2D):
            return Pt2D(self._x + p2._x, self._y + p2._y)
        # assume value that can be applied piecewise
        return Pt2D(self._x + p2, self._y + p2)

    def __sub__(self, p2):
        if isinstance(p2, Pt2D):
            return Pt2D(self._x - p2._x, self._y - p2._y)
        # assume value that can be applied piecewise
        return Pt2D(self._x - p2, self._y - p2)

    def __truediv__(self, p2):

        # assume value that can be applied piecewise
        return Pt2D(self._x / p2, self._y / p2)

    def __mul__(self, p2):

        # assume value that can be applied piecewise
        return Pt2D(self._x * p2, self._y * p2)

    @staticmethod
    def copy(pt):
        """Create a copy of a Pt2D object.

        Args:
            pt (Pt2D): Point to copy.

        Returns:
            Pt2D: A copy of pt.
        """
        return pt.clone()

    def clone(self):
        """Create a duplicate of this point.

        Returns:
            Pt2D: A copy of this point.
        """
        return Pt2D(self._x, self._y)

    @property
    def x(self):
        """float: The x-coordinate of the point."""
        return self._x

    @property
    def y(self):
        """float: The y-coordinate of the point."""
        return self._y

    @x.setter
    def x(self, val):
        self._x = val

    @y.setter
    def y(self, val):
        self._y = val


#######################################################################
class BaseSegment(ABC):
    """Abstract Base Class that defines the interface for all segment objects.

    Args:
        pt1 (Pt2D): The first endpoint of the segment.
        pt2 (Pt2D): The second endpoint of the segment.

    Raises:
        TypeError: If either pt1 or pt2 is not a Pt2D.
    """

    # concrete methods
    def __init__(self, pt1, pt2):

        if not isinstance(pt1, Pt2D) or not isinstance(pt2, Pt2D):
            raise TypeError('Both points must be of type Pt2D')

        # ensure points are in proper x-order
        if pt1.x <= pt2.x:
            self._lowPt = pt1
            self._highPt = pt2
        else:
            self._lowPt = pt2
            self._highPt = pt1

        super(BaseSegment, self).__init__()

    def __getitem__(self, ind):
        if ind >= 2 or ind < 0:
            raise IndexError('Index must be 0 or 1')
        return self._lowPt if ind == 0 else self._highPt

    def __len__(self):
        return 2

    def __eq__(self, rhs):
        # be sure to override for any additional comparisons
        return isinstance(BaseSegment, rhs) and self._lowPt == rhs._lowPt and self._highPt == rhs._highPt

    def x_inrange(self, xval):
        """Test to see if x-value is between x-values of line segment.
        
        Args:
            xval (float): The x-value to test.

        Returns:
            bool: True if xVal falls within range of the segment; False otherwise.
        """

        return self._lowPt.x <= xval <= self._highPt.x

    @property
    def leftpoint(self):
        """Pt2D: The leftmost point of the segment."""
        return self._lowPt

    @property
    def rightpoint(self):
        """Pt2D: The rightmost point of the segment."""
        return self._highPt

    @leftpoint.setter
    def leftpoint(self, pt):
        self._lowPt = pt
        if self._lowPt == self._highPt:
            raise ValueError('Points are equal; Zero-length line')

    @rightpoint.setter
    def rightpoint(self, pt):
        self._highPt = pt
        if self._lowPt == self._highPt:
            raise ValueError('Points are equal; Zero-length line')

    # abstract methods

    @abstractmethod
    def y_for_x(self, x):
        """Retrieve the y value for a provide x value; basically calling 
             f(x) for the segment.

        Args:
            x (float): The value to query with.

        Returns:
            float: The value for processing x.
        """
        pass

    def __call__(self, x):
        return self.y_for_x(x)

    @abstractmethod
    def split(self, ratio=0.5):
        """split a segment into two sub-segments.

        Args:
            ratio (float): The relative position of the point of the split, within range [0,1].

        Reurns:
            tuple: Two segments that represent the split segment.
        """
        pass

    @abstractmethod
    def subsegment(self, x1, x2):
        """Derive a subsegment from this segment.

            Args:
                x1 (float): The leftmost x-location of the subsegment.
                x2 (float): The rightmost x-location of the subsegment.

            Returns:
                float: A subsegment defined by the provided x-boundaries.
        """
        pass

    @property
    @abstractmethod
    def maxpoint(self):
        """Pt2D: point with the largest y value.
        """
        pass

    @property
    @abstractmethod
    def minpoint(self):
        """Pt2D: Point with the smallest y value.
        """
        pass

    @property
    @abstractmethod
    def equation_args(self):
        """dict: Key-value pairs representing additional equation arguments."""
        pass

    @equation_args.setter
    @abstractmethod
    def equation_args(self, dargs):
        pass

    @property
    def drawpoints(self):
        """ list: Enough points to draw the segment."""
        pts = []
        for i in range(513):
            ratio = i / 512.
            x = (self._lowPt.x * (1. - ratio)) + (self._highPt.x * ratio)
            pts.append(Pt2D(x, self(x)))

        return pts

    @property
    def ctrlpoints(self):
        """list: Points that aren't part of the line, but influence the shape."""

        return []


#######################################################################
#
# ACTIVE SEGMENTS
#

class LinearSegment(BaseSegment):
    """Straight forward implementation of a linear line segment.

    Args:
        pt1 (Pt2D): The first endpoint of the segment.
        pt2 (Pt2D): The second endpoint of the segment.

    See Also:
        BaseSegment for documentation on inherited properties, attributes, and methods.
    """

    def __init__(self, pt1, pt2):

        BaseSegment.__init__(self, pt1, pt2)

        if pt1 == pt2:
            raise ValueError('Points are equal; Zero-length line')

        self.refresh_coefficients()

    def refresh_coefficients(self):
        """refresh the reference coefficients to match the points provided.
        """
        if self._highPt.x != self._lowPt.x:
            self._m = (self._highPt.y - self._lowPt.y) / (self._highPt.x - self._lowPt.x)
            self._b = self._lowPt.y - (self._m * self._lowPt.x)
        else:
            self._m = None
            self._b = None

    def __repr__(self):
        return '{0}---{1}'.format(self._lowPt.__repr__(), self._highPt.__repr__())

    def __eq__(self, rhs):
        if rhs is None:
            return False
        return (self._lowPt == rhs._lowPt and
                self._highPt == rhs._highPt)

    def y_for_x(self, x):
        """Retrieve the y value for a provide x value; basically calling
             f(x) for the segment.

        Args:
            x (float): The value to query with.

        Returns:
            float: The value for processing x.
        """
        return self._m * x + self._b

    def split(self, ratio=0.5):
        """split a segment into two sub-segments.

        Args:
            ratio (float): The relative position of the point of the split, within range [0,1].

        Returns:
            tuple: Two segments that represent the split segment.
        """
        lhs = None
        rhs = None

        mp = self._lowPt * (1 - ratio) + self._highPt * ratio

        if ratio > 0:
            lhs = LinearSegment(self._lowPt.clone(), mp)

        if ratio < 1.0:
            rhs = LinearSegment(mp, self._highPt.clone())

        return lhs, rhs

    def subsegment(self, x1, x2):
        """Derive a subsegment from this segment.

            Args:
                x1 (float): The leftmost x-location of the subsegment.
                x2 (float): The rightmost x-location of the subsegment.

            Returns:
                float: A subsegment defined by the provided x-boundaries.
        """
        return LinearSegment(Pt2D(x1, self(x1)), Pt2D(x2, self(x2)))

    @property
    def maxpoint(self):
        """Pt2D: point with the largest y value."""
        ret = self._lowPt if self._lowPt.y > self._highPt.y else self._highPt
        return ret.clone()

    @property
    def minpoint(self):
        """Pt2D: Point with the smallest y value."""
        ret = self._lowPt if self._lowPt.y <= self._highPt.y else self._highPt
        return ret.clone()

    @property
    def equation_args(self):
        """dict: Key-value pairs representing additional equation arguments."""
        return {}

    @equation_args.setter
    def equation_args(self, dargs):
        pass

    @property
    def drawpoints(self):
        """ list: Enough points to draw the segment."""
        return [self._lowPt, self._highPt]

    @property
    def lowpoint(self):
        """float: y value for lowest x-ordinate"""
        return self._lowPt

    @property
    def highpoint(self):
        """float: y value for highest x-ordinate"""

        return self._highPt


#######################################################################
class StepwiseSegment(BaseSegment):
    """ Line segment representation that is discontinuous with the rest of the curve.

    Control Points are where adjacent points are picked up; actual shelf is determined
    by height value.

    Attributes:
        height (float): The height of the horizontal line.

    Args:
        pt1 (Pt2D): The first endpoint of the segment.
        pt2 (Pt2D): The second endpoint of the segment.
        height (float, optional): The height of the step. If None, defaults to mid-height between pt1 and pt2.

    See Also:
        BaseSegment for documentation on inherited properties, attributes, and methods.
    """

    def __init__(self, pt1, pt2, height=None):

        BaseSegment.__init__(self, pt1, pt2)

        if height is not None:
            self.height = height
        else:
            self.height = (pt1.y + pt2.y) / 2

        # ensure that points are sorted
        self._lowPt = pt1 if pt1.x <= pt2.x else pt2
        self._highPt = pt2 if pt2.x >= pt1.x else pt1

    def __repr__(self):
        return '{0}|{1}|{2}'.format(self._lowPt.__repr__(), self.height, self._highPt.__repr__())

    def __eq__(self, rhs):
        if rhs is None:
            return False
        if not isinstance(rhs, StepwiseSegment):
            return False
        return (self._lowPt == rhs._lowPt and
                self._highPt == rhs._highPt) and self.height == rhs.height

    def y_for_x(self, x):
        """Retrieve the y value for a provide x value; basically calling
             f(x) for the segment.

        Args:
            x (float): The value to query with.

        Returns:
            float: The value for processing x.
        """
        return self.height

    def subsegment(self, x1, x2):
        """Derive a subsegment from this segment.

            Args:
                x1 (float): The leftmost x-location of the subsegment.
                x2 (float): The rightmost x-location of the subsegment.

            Returns:
                float: A subsegment defined by the provided x-boundaries.
        """
        return StepwiseSegment(Pt2D(x1, self.height), Pt2D(x2, self.height), self.height)

    def split(self, ratio=0.5):
        """split a segment into two sub-segments.

        Args:
            ratio (float): The relative position of the point of the split, within range [0,1].

        Reurns:
            tuple: Two segments that represent the split segment.
        """
        lhs = None
        rhs = None

        mp = self._lowPt * (1 - ratio) + self._highPt * ratio

        if ratio > 0:
            lhs = StepwiseSegment(self._lowPt, mp, self.height)

        if ratio < 1.0:
            rhs = StepwiseSegment(mp, self._highPt, self.height)

        return lhs, rhs

    @property
    def maxpoint(self):
        """Pt2D: point with the largest y value."""
        return Pt2D(self._hightPt.x, self.height)

    @property
    def minpoint(self):
        """Pt2D: Point with the smallest y value."""
        return Pt2D(self._lowPt.x, self.height)

    @property
    def equation_args(self):
        """dict: Key-value pairs representing additional equation arguments."""
        return {'height': self.height}

    @equation_args.setter
    def equation_args(self, dargs):

        if isinstance(dargs, list):
            for i in range(0, len(dargs), 2):
                setattr(self, dargs[i], dargs[i + 1])
        else:
            for k, v in dargs.items():
                setattr(self, k, v)

    @property
    def drawpoints(self):
        """ return enough points to draw accurately."""
        return [Pt2D(self._lowPt.x, self.height), Pt2D(self._highPt.x, self.height)]


#######################################################################

class BezierSegment(BaseSegment):
    """A segment defined as a bezier curve.

    Args:
        pt1 (Pt2D): The first endpoint of the segment.
        pt2 (Pt2D): The second endpoint of the segment.
        ctrl1 (Pt2D, optional): The point controlling the shape of the curve. If None, defaults to midpoint along linear
          segment between pt1 and pt2.

    Raises:
        ValueError: If pt1 and pt2 are equal.

    See Also:
        BaseSegment for documentation on inherited properties, attributes, and methods.
    """

    def __init__(self, pt1, pt2, ctrl1=None):
        BaseSegment.__init__(self, pt1, pt2)

        if pt1 == pt2:
            raise ValueError('Points are equal; Zero-length line')

        self._ctrl1 = ctrl1
        if self._ctrl1 is None:
            # pick midpoint
            self._ctrl1 = (pt1 + pt2) * 0.5

    def __repr__(self):
        return '{0}S{1}'.format(self._lowPt.__repr__(), self._highPt.__repr__())

    def __eq__(self, rhs):
        if rhs is None:
            return False
        if not isinstance(rhs, BezierSegment):
            return False

        return (self._lowPt == rhs._lowPt and
                self._highPt == rhs._highPt) and self._ctrl1 == rhs._ctrl1

    def y_for_x(self, x):
        """Retrieve the y value for a provide x value; basically calling
             f(x) for the segment.

        Args:
            x (float): The value to query with.

        Returns:
            float: The value for processing x.
        """
        # find relative position along curve

        t = 0.5
        if self._ctrl1.x > x:
            t = 0.5 - t * (self._ctrl1.x - x) / (self._ctrl1.x - self._lowPt.x)
        elif self._ctrl1.x < x:
            t = 0.5 + t * ((x - self._ctrl1.x) / (self._highPt.x - self._ctrl1.x))

        alt_t = 1 - t
        return ((alt_t ** 2) * self._lowPt.y) + (2 * t * alt_t * self._ctrl1.y) + ((t ** 2) * self._highPt.y)

    def split(self, ratio=0.5):
        """split a segment into two sub-segments.

        Args:
            ratio (float): The relative position of the point of the split, within range [0,1].

        Reurns:
            tuple: Two segments that represent the split segment.
        """
        # https://math.stackexchange.com/questions/1408478/subdividing-a-b%C3%A9zier-curve-into-n-curves
        lhs = None
        rhs = None

        alt_ratio = 1 - ratio
        if ratio > 0:
            leftctrl = (self._lowPt * alt_ratio) + (self._ctrl1 * ratio)
            lefthigh = (self._lowPt * (alt_ratio ** 2)) + (self._ctrl1 * 2 * ratio * alt_ratio) + (
                    self._highPt * (ratio ** 2))
            lhs = BezierSegment(self._lowPt, lefthigh, leftctrl)

        if ratio < 1.0:
            rightlow = (self._lowPt * (alt_ratio ** 2)) + (self._ctrl1 * 2 * ratio * alt_ratio) + (
                    self._highPt * (ratio ** 2))
            rightctrl = (self._ctrl1 * alt_ratio) + (self._highPt * ratio)
            rhs = BezierSegment(rightlow, self._highPt, rightctrl)

        return lhs, rhs

    def subsegment(self, x1, x2):
        """Derive a subsegment from this segment.

            Args:
                x1 (float): The leftmost x-location of the subsegment.
                x2 (float): The rightmost x-location of the subsegment.

            Returns:
                float: A subsegment defined by the provided x-boundaries.
        """
        r1 = (x1 - self._lowPt.x) / (self._highPt.x - self._lowPt.x)
        r2 = (x2 - self._lowPt.x) / (self._highPt.x - self._lowPt.x)

        p1 = Pt2D(r1, self(r1))
        p2 = Pt2D(r2, self(r2))

        return BezierSegment(p1, p2, self._ctrl1)

    @property
    def equation_args(self):
        """dict: Key-value pairs representing additional equation arguments."""
        return {'xadjust': self._ctrl1.x,
                'yadjust': self._ctrl1.y}

    @equation_args.setter
    def equation_args(self, dargs):

        if isinstance(dargs, list):
            for i in range(0, len(dargs), 2):
                setattr(self, dargs[i], dargs[i + 1])
        else:
            for k, v in dargs.items():
                setattr(self, k, v)

    @property
    def maxpoint(self):
        """Pt2D: point with the largest y value."""
        test1 = self._lowPt if self._lowPt.y > self._highPt else self._highPt

        midx = (self._lowPt.x + self._highPt.x) / 2.0
        midy = self(midx)
        if test1.y > midy or (test1.y == midy and test1.x > midx):
            ret = test1.clone()
        else:
            ret = Pt2D(midx, midy)

        return ret

    @property
    def minpoint(self):
        """Pt2D: Point with the smallest y value."""
        test1 = self._lowPt if self._lowPt.y <= self._highPt else self._highPt

        midx = (self._lowPt.x + self._highPt.x) / 2.0
        midy = self(midx)
        if test1.y <= midy or (test1.y == midy and test1.x <= midx):
            ret = test1.clone()
        else:
            ret = Pt2D(midx, midy)

        return ret

    @property
    def xadjust(self):
        """float: The x-value of the control point."""
        return self._ctrl1.x

    @property
    def yadjust(self):
        """float: The y-value of the control point."""
        return self._ctrl1.y

    @xadjust.setter
    def xadjust(self, x):
        self._ctrl1.x = x

    @yadjust.setter
    def yadjust(self, y):
        self._ctrl1.y = y

    @property
    def ctrlpoints(self):
        """list: Points that aren't part of the line, but influence the shape."""
        return [self._ctrl1]


#######################################################################
#
# Module level utilities
#

def to_pt2d(invals):
    """Convert Python container to Pt2D object.
    
    Args:
        invals (object): The python container with the x,y values in the first two indices.

    Returns:
        Pt2D: Point with values of invals[0:1].
    """
    return Pt2D(invals[0], invals[1])
