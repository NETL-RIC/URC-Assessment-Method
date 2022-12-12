"""Module containing various implementations of FuzzyCurve types.

Author: Patrick Wingo

Version: 0.1

"""

from __future__ import absolute_import, division, print_function, unicode_literals
import sys
from math import floor, exp
from .geomutils import *
from .nodata_handling import NoDataSentinel
from .geomutils import bounds_check

import copy
from abc import abstractmethod

if sys.version_info[0] != 3:
    from abc import ABCMeta

    # Trick from:
    # https://stackoverflow.com/questions/35673474/using-abc-abcmeta-in-a-way-it-is-compatible-both-with-python-2-7-and-python-3-5
    ABC = ABCMeta(str('ABC'), (object,), {'__slots__': ()})

    inf = float('inf')
else:
    from abc import ABC
    from math import inf


#######################################################################


class FuzzyCurve(ABC):
    """A partially abstract class for all Curve types to inherit from.

    Attributes:
        name (str): The name associated with the curve.
        monotonic (boolean): **Class attribute**; specifies if the curve is monotonic when processed.


    Args:
        name (str): The name to assign to the curve.

    """

    monotonic = False

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """
        pass

    def copy_segments(self):
        """Create a discrete copy of the segments that compose the curve.

        Returns:
            list: An explicit copy of all internal segments.
        """
        return copy.deepcopy(list(self._segments))

    def overwrite_segments(self, segs):
        """Replace the curve segments with an explicit copy of the supplied segments.

        Args:
            segs (list): The segments to copy and use.
        """
        self._segments = copy.deepcopy(tuple(segs))

    @staticmethod
    def _ensure_end_to_end(segs):
        """Makes sure that all endpoints of the segments overlap, and that the entire x-range is [0,1]

        Args:
            segs (list): Segments to be processed; on return, x endpoints will have been adjusted to
              properly overlap.
        """

        if len(segs) > 0:

            for i in range(1, len(segs)):
                # use absolute equality here
                if segs[i].leftpoint.x != segs[i - 1].rightpoint.x:
                    segs[i].leftpoint = Pt2D(segs[i - 1].rightpoint.x, segs[i](segs[i - 1].rightpoint.x))

            # ensure [0,1]
            segs[0].leftpoint = Pt2D(0.0, segs[0](0.0))
            segs[-1].rightpoint = Pt2D(1.0, segs[-1](1.0))

    @property
    def ctrlpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """
        return []

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """
        return []

    @property
    def drawpoints(self):
        """ list: Enough points to draw the segment."""
        pts = []
        for i in range(513):
            x = i / 512.
            pts.append(Pt2D(x, self(x)))

        return pts

    @abstractmethod
    def construct_multiple(self, count, overlap, midpoint_to_edge):
        """Construct multiple copies of this FuzzyCurve, distributing based on the method arguments.

        Args:
            count (int): The number of curves to produce; minimum of 2.
            overlap (float): Rough percentage of overlap between curves; in the range of [0,1].
            midpoint_to_edge (boolean): If true, the first and last curves will have their midpoints shifted to either
                                      edge of the graph space, with additional curves spaced appropriately.

        Raises:
            ValueError: If `count` is less than 2.

        """
        pass

    def multiple_allow_overlap(self):
        """Flag indicating whether or not multiple instances can overlap when templated.

        Returns:
            bool: True if overlapping is allowed; False otherwise.
        """

        return True


#######################################################################
class LinearCurve(FuzzyCurve):
    """A simple curve class for representing linearly increasing or decreasing membership functions.

    Attributes:
        name (str): The name associated with the curve.
        monotonic (boolean): **Class attribute**; specifies if the curve is monotonic when processed.


    Args:
        name (str): The name to assign to the curve.

    """

    monotonic = True

    def __init__(self, name):
        FuzzyCurve.__init__(self, name)

        self._segment = LinearSegment(Pt2D(0.0), Pt2D(1., 1.))

    def __repr__(self):
        return self._segment.__repr__()

    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """
        if inval <= self._segment._lowPt.x:
            return self._segment._lowPt.y
        if inval >= self._segment._highPt.x:
            return self._segment._highPt.y

        return self._segment.y_for_x(inval)

    @property
    def xleft(self):
        """float: X-coordinate of leftmost point of the curve."""
        return self._segment._lowPt.x

    @property
    def xright(self):
        """float: X-coordinate of the rightmost point of the curve."""
        return self._segment._highPt.x

    @property
    def yleft(self):
        """float: Y-coordinate of leftmost point of the curve."""
        return self._segment._lowPt.y

    @property
    def yright(self):
        """float: Y-coordinate of the rightmost point of the curve."""
        return self._segment._highPt.y

    @xleft.setter
    def xleft(self, x):
        self._segment._lowPt.x = x
        self._segment.refresh_coefficients()

    @xright.setter
    def xright(self, x):
        self._segment._highPt.x = x
        self._segment.refresh_coefficients()

    @yleft.setter
    def yleft(self, y):
        self._segment._lowPt.y = y
        self._segment.refresh_coefficients()

    @yright.setter
    def yright(self, y):
        self._segment._highPt.y = y
        self._segment.refresh_coefficients()

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """
        return self._segment.drawpoints

    @property
    def drawpoints(self):
        """list: geomutils.Pt2D objects that can be used to trace the curve in a visual display.
        """
        midpoints = self._segment.drawpoints
        return [Pt2D(0.0, midpoints[0].y)] + midpoints + [Pt2D(1.0, midpoints[1].y)]

    def construct_multiple(self, count, overlap, midpoint_to_edge):
        """Construct multiple copies of this FuzzyCurve, distributing based on the method arguments.

        Args:
            count (int): The number of curves to produce; minimum of 2.
            overlap (float): Rough percentage of overlap between curves; in the range of [0,1].
            midpoint_to_edge (boolean): If true, the first and last curves will have their midpoints shifted to either
                                      edge of the graph space, with additional curves spaced appropriately.

        Raises:
            ValueError: If `count` is less than 2.

        """

        if count < 2:
            raise ValueError('At least two curves must be requested')

        basesize = 1.0 / (count if not midpoint_to_edge else (count - 1))
        slicesize = 2 * overlap * basesize + basesize
        offs = slicesize / 2
        midx = basesize / 2 if not midpoint_to_edge else 0

        ret = []
        for i in range(count):
            dup = copy.deepcopy(self)
            curr_mid = midx + basesize * i

            dup.xleft = curr_mid - offs
            dup.xright = dup.xleft + slicesize
            ret.append(dup)

        return ret


#######################################################################

class GaussianCurve(FuzzyCurve):
    """A curve that conforms to the equation: :math:`f(x)=ae^{-\\frac{(x-b)^2}{2c^2}}`.

    Where:
       - **a** is the height of the bell.
       - **b** is the center of the bell.
       - **c** is the "width" of the bell.

    Attributes:
        name (str): The name associated with the curve.
        monotonic (boolean): **Class attribute**; specifies if the curve is monotonic when processed.


    Args:
        name (str): The name to assign to the curve.

    """

    def __init__(self, name):
        FuzzyCurve.__init__(self, name)

        # https://en.wikipedia.org/wiki/Gaussian_function
        # a is height
        # b is center of peak
        # c is "width" of bell
        self._a = 1.0
        self._b = 0.5
        self._c = 0.1
        self._yOffset = 0.0
        self._refresh_c_denom()

    def __repr__(self):
        return "a={0}, b={1}, c={2}, yOffs={3}".format(self._a, self._b, self._c, self._yOffset)

    def __str__(self):
        return "x-midpoint={0}, spread={1}, y-minimum={2}, y-maximum={3}".format(self.xmidpoint, self.spread, self.ymin,
                                                                                 self.ymax)

    def _refresh_c_denom(self):
        self._cDenom = 2 * (self._c ** 2)

    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """

        exponent = -((inval - self._b) ** 2) / self._cDenom

        return ((self._a - self._yOffset) * exp(exponent)) + self._yOffset

    @property
    def xmidpoint(self):
        """float: The midpoint/apex of the \"bell\" of the functions."""
        return self._b

    @property
    def spread(self):
        """float: Value that controls the width of the \"bell\"."""
        return self._c

    @property
    def ymin(self):
        """float: The lower y-axis value boundary."""
        return self._yOffset

    @property
    def ymax(self):
        """float: The upper y-axis value boundary."""
        return self._a

    @xmidpoint.setter
    def xmidpoint(self, x):
        self._b = x

    @spread.setter
    def spread(self, width):
        self._c = width
        self._refresh_c_denom()

    @ymin.setter
    def ymin(self, y):
        self._yOffset = y

    @ymax.setter
    def ymax(self, y):
        self._a = y

    @property
    def ctrlpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """

        hext = self._c / 2
        xleft = self._b - hext
        xright = self._b + hext
        return [Pt2D(xleft, self(xleft)), Pt2D(xright, self(xright))]

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """

        # xleft=max(0.0,self._b-(4*self._c))
        # xright=min(1.0,self._b+(4*self._c))
        xleft = max(0.0, self._b - 3.5 * self._c)
        xright = min(1.0, self._b + 3.5 * self._c)
        return [Pt2D(xleft, self(xleft)), Pt2D(self._b, self._a), Pt2D(xright, self(xright))]

    def construct_multiple(self, count, overlap, midpoint_to_edge):
        """Construct multiple copies of this FuzzyCurve, distributing based on the method arguments.

        Args:
            count (int): The number of curves to produce; minimum of 2.
            overlap (float): Rough percentage of overlap between curves; in the range of [0,1].
            midpoint_to_edge (boolean): If true, the first and last curves will have their midpoints shifted to either
                                      edge of the graph space, with additional curves spaced appropriately.

        Raises:
            ValueError: If `count` is less than 2.

        """

        if count < 2:
            raise ValueError('At least two curves must be requested')

        spread = (1 / (7 * count))
        slicesize = 1 / count
        startx = slicesize / 2
        if midpoint_to_edge:
            spread = 1 / (7 * (count - 1))
            slicesize = 1 / (count - 1)
            startx = 0.0

        spread += 4 * spread * overlap
        ret = []
        for i in range(count):
            dup = copy.deepcopy(self)
            leftx = startx + (slicesize * i)

            dup.xmidpoint = leftx
            # spread here
            dup.spread = spread
            ret.append(dup)

        return ret


#######################################################################

class SigmoidCurve(FuzzyCurve):
    """A curve that conforms to the equation: :math:`f(x) = \\frac{L}{1+e^{-k(x-x0)}}`.

    Where:
       - **x0** is the x-coordinate of the midpoint between upper and lower boundaries.
       - **L** is the maximum y-value.
       - **k** is the "steepness" of the slope of the curve.

    Attributes:
        name (str): The name associated with the curve.
        monotonic (boolean): **Class attribute**; specifies if the curve is monotonic when processed.


    Args:
        name (str): The name to assign to the curve.

    """

    monotonic = True

    def __init__(self, name):
        FuzzyCurve.__init__(self, name)

        # https://en.wikipedia.org/wiki/Logistic_function
        # x0 is midpoint
        # L is y max
        # k is steepness of curve

        self._x0 = .5
        self._L = 1.0
        self._k = 20.0
        self._yOffset = 0.0

    def __repr__(self):
        return "x0={0}, L={1}, k={2}, yOffs={3}".format(self._x0, self._L, self._k, self._yOffset)

    def __str__(self):
        return "x-midpoint={0}, slope={1}, y-minimum={2}, y-maximum={3}".format(self.xmidpoint, self.slope, self.ymin,
                                                                                self.ymax)

    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """

        return ((self._L - self._yOffset) / (1 + exp(-self._k * (inval - self._x0)))) + self._yOffset
        # return self._L / (1 + exp(-self._k * (inval - self._x0)))
        # return 1 / (1 + exp(-inval))

    @property
    def xmidpoint(self):
        """float: The x-coordinate of the point halfway between the y-coordinate boundaries."""
        return self._x0

    @property
    def slope(self):
        """float: The "steepness" of the increase in the equation."""
        return self._k

    @property
    def ymin(self):
        """float: The lower y-axis value boundary."""
        return self._yOffset

    @property
    def ymax(self):
        """float: The upper y-axis value boundary."""
        return self._L

    @xmidpoint.setter
    def xmidpoint(self, x):
        self._x0 = x

    @slope.setter
    def slope(self, slp):
        self._k = slp

    @ymin.setter
    def ymin(self, y):
        self._yOffset = y

    @ymax.setter
    def ymax(self, y):
        self._L = y

    @property
    def ctrlpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """
        return [Pt2D(self._x0, self(self._x0))]

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """

        return [Pt2D(0.0, self(0.0)), Pt2D(self._k, self(self._k)), Pt2D(1.0, self(1.0))]

    def construct_multiple(self, count, overlap, midpoint_to_edge):
        """Construct multiple copies of this FuzzyCurve, distributing based on the method arguments.

        Args:
            count (int): The number of curves to produce; minimum of 2.
            overlap (float): Rough percentage of overlap between curves; in the range of [0,1].
            midpoint_to_edge (boolean): If true, the first and last curves will have their midpoints shifted to either
                                      edge of the graph space, with additional curves spaced appropriately.

        Raises:
            ValueError: If `count` is less than 2.

        """

        if count < 2:
            raise ValueError('At least two curves must be requested')

        slicesize = 1 / count
        startx = slicesize / 2
        if midpoint_to_edge:
            slicesize = 1 / (count - 1)
            startx = 0.0

        baseslope = 24 * (count - 1)

        ret = []
        for i in range(count):
            dup = copy.deepcopy(self)
            leftx = startx + (slicesize * i)

            dup.xmidpoint = leftx
            dup.slope = baseslope - (baseslope * overlap)
            ret.append(dup)

        return ret


#######################################################################

class TriangleCurve(FuzzyCurve):
    """A curve with a singular triangle/pyramid shape.

    Attributes:
        name (str): The name associated with the curve.
        monotonic (boolean): **Class attribute**; specifies if the curve is monotonic when processed.

    Args:
        name (str): The name to assign to the curve.

    """

    def __init__(self, name):
        FuzzyCurve.__init__(self, name)

        leftpt = Pt2D(0.25, 0.0)
        midpt = Pt2D(0.5, 1.0)
        rightpt = Pt2D(0.75, 0.0)
        self._leftSeg = LinearSegment(leftpt, midpt)
        self._rightSeg = LinearSegment(midpt, rightpt)

    def __repr__(self):
        return "{0}/{1}\\{2}".format(self._leftSeg.leftpoint, self._leftSeg.rightpoint, self._rightSeg.rightpoint)

    def __str__(self):
        return "x-midpoint={0}, slope={1}, y-minimum={2}, y-maximum={3}".format(self.xmidpoint, self.spread, self.ymin,
                                                                                self.ymax)

    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """

        if inval <= self._leftSeg._lowPt.x or inval >= self._rightSeg._highPt.x:
            return self._leftSeg._lowPt.y
        elif inval <= self._leftSeg._highPt.x:
            return self._leftSeg(inval)

        return self._rightSeg(inval)

    @property
    def xmidpoint(self):
        """float: X-coordinate of the apex of the triangle curve."""
        return self._leftSeg.rightpoint.x

    @property
    def spread(self):
        """float: The width of the triangle base."""
        return self._rightSeg.rightpoint.x - self._leftSeg.leftpoint.x

    @property
    def ymin(self):
        """float: The lower y-axis value boundary."""
        return self._leftSeg.leftpoint.y

    @property
    def ymax(self):
        """float: The upper y-axis value boundary."""
        return self._rightSeg.leftpoint.y

    @xmidpoint.setter
    def xmidpoint(self, x):
        # find difference
        oldx = self._leftSeg.rightpoint.x
        diff = x - oldx
        self._leftSeg.leftpoint.x += diff
        self._leftSeg.rightpoint.x = x
        self._rightSeg.leftpoint.x = x
        self._rightSeg.rightpoint.x += diff

        self._leftSeg.refresh_coefficients()
        self._rightSeg.refresh_coefficients()

    @spread.setter
    def spread(self, width):

        halfext = width / 2.0
        self._leftSeg.leftpoint.x = self._leftSeg.rightpoint.x - halfext
        self._rightSeg.rightpoint.x = self._rightSeg.leftpoint.x + halfext
        self._leftSeg.refresh_coefficients()
        self._rightSeg.refresh_coefficients()

    @ymin.setter
    def ymin(self, y):
        self._leftSeg.leftpoint.y = y
        self._rightSeg.rightpoint.y = y
        self._leftSeg.refresh_coefficients()
        self._rightSeg.refresh_coefficients()

    @ymax.setter
    def ymax(self, y):
        self._leftSeg.rightpoint.y = y
        self._rightSeg.leftpoint.y = y
        self._leftSeg.refresh_coefficients()
        self._rightSeg.refresh_coefficients()

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """

        return [self._leftSeg.leftpoint, self._leftSeg.rightpoint, self._rightSeg.rightpoint]

    @property
    def drawpoints(self):
        """list: geomutils.Pt2D objects that can be used to trace the curve in a visual display.
        """

        return [Pt2D(0.0, self(0.0))] + self.anchorpoints + [Pt2D(1.0, self(1.0))]

    def construct_multiple(self, count, overlap, midpoint_to_edge):
        """Construct multiple copies of this FuzzyCurve, distributing based on the method arguments.

        Args:
            count (int): The number of curves to produce; minimum of 2.
            overlap (float): Rough percentage of overlap between curves; in the range of [0,1].
            midpoint_to_edge (boolean): If true, the first and last curves will have their midpoints shifted to either
                                      edge of the graph space, with additional curves spaced appropriately.

        Raises:
            ValueError: If `count` is less than 2.

        """

        if count < 2:
            raise ValueError('At least two curves must be requested')

        slicesize = 1 / count
        startx = slicesize / 2
        if midpoint_to_edge:
            slicesize = 1 / (count - 1)
            startx = 0.0

        ret = []
        for i in range(count):
            dup = copy.deepcopy(self)
            leftx = startx + (slicesize * i)

            dup.xmidpoint = leftx
            dup.spread = slicesize + (overlap * slicesize * 2)
            # spread here
            ret.append(dup)

        return ret


#######################################################################

class TrapezoidCurve(FuzzyCurve):
    """A curve with a trapezoid shape.

    Attributes:
        name (str): The name associated with the curve.
        monotonic (boolean): **Class attribute**; specifies if the curve is monotonic when processed.

    Args:
        name (str): The name to assign to the curve.

    """

    def __init__(self, name):
        FuzzyCurve.__init__(self, name)

        self._leftSeg = LinearSegment(Pt2D(0.0, 0.0), Pt2D(0.3, 1.0))
        self._midSeg = LinearSegment(Pt2D(0.3, 1.0), Pt2D(0.7, 1.0))
        self._rightSeg = LinearSegment(Pt2D(0.7, 1.0), Pt2D(1.0, 0.0))

    def __repr__(self):
        return "{0}/{1}--{2}\\{3}".format(self._leftSeg.leftpoint, self._leftSeg.rightpoint, self._midSeg.rightpoint,
                                          self._rightSeg.rightpoint)

    def __str__(self):
        return "x-midpoint={0}, low-spread={1}, high-spread={2},y-minimum={3}, y-maximum={4}".format(self.xmidpoint,
                                                                                                     self.lowspread,
                                                                                                     self.highspread,
                                                                                                     self.ymin,
                                                                                                     self.ymax)

    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """

        if inval <= self._leftSeg._lowPt.x or inval >= self._rightSeg._highPt.x:
            return self._leftSeg._lowPt.y
        elif inval <= self._leftSeg._highPt.x:
            return self._leftSeg(inval)
        elif inval <= self._midSeg._highPt.x:
            return self._midSeg(inval)

        return self._rightSeg(inval)

    @property
    def xmidpoint(self):
        """float: X-coordinate of the midpoint of the trapezoid."""
        return (self._midSeg.maxpoint.x + self._midSeg.minpoint.x) / 2.0

    @property
    def lowspread(self):
        """float: Width of the base of the trapezoid."""
        return self._rightSeg.rightpoint.x - self._leftSeg.leftpoint.x

    @property
    def highspread(self):
        """float: width of the upper portion of the trapezoid."""
        return self._midSeg.rightpoint.x - self._midSeg.leftpoint.x

    @property
    def ymin(self):
        """float: The lower y-axis value boundary."""
        return self._leftSeg.leftpoint.y

    @property
    def ymax(self):
        """float: The upper y-axis value boundary."""
        return self._midSeg.leftpoint.y

    @xmidpoint.setter
    def xmidpoint(self, x):
        lowhext = self.lowspread / 2.0
        highhext = self.highspread / 2.0
        pt1 = Pt2D(x - lowhext, self.ymin)
        pt2 = Pt2D(x - highhext, self.ymax)
        pt3 = Pt2D(x + highhext, self.ymax)
        pt4 = Pt2D(x + lowhext, self.ymin)

        self._leftSeg = LinearSegment(pt1, pt2)
        self._midSeg = LinearSegment(pt2, pt3)
        self._rightSeg = LinearSegment(pt3, pt4)

    @lowspread.setter
    def lowspread(self, width):

        halfext = width / 2.0
        xmid = self.xmidpoint
        self._leftSeg.leftpoint.x = xmid - halfext
        self._rightSeg.rightpoint.x = xmid + halfext
        self._leftSeg.refresh_coefficients()
        self._rightSeg.refresh_coefficients()

    @highspread.setter
    def highspread(self, width):

        halfext = width / 2.0
        xmid = self.xmidpoint
        self._midSeg.leftpoint.x = xmid - halfext
        self._midSeg.rightpoint.x = xmid + halfext

        self._leftSeg.rightpoint.x = self._midSeg.leftpoint.x
        self._rightSeg.leftpoint.x = self._midSeg.rightpoint.x

        self._leftSeg.refresh_coefficients()
        self._rightSeg.refresh_coefficients()

    @ymin.setter
    def ymin(self, y):
        self._leftSeg.leftpoint.y = y
        self._rightSeg.rightpoint.y = y

        self._leftSeg.refresh_coefficients()
        self._rightSeg.refresh_coefficients()

    @ymax.setter
    def ymax(self, y):
        self._leftSeg.rightpoint.y = y
        self._rightSeg.leftpoint.y = y

        self._midSeg.leftpoint.y = y
        self._midSeg.rightpoint.y = y

        self._leftSeg.refresh_coefficients()
        self._rightSeg.refresh_coefficients()
        self._midSeg.refresh_coefficients()

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """

        return [self._leftSeg.leftpoint, self._leftSeg.rightpoint, self._midSeg.rightpoint, self._rightSeg.rightpoint]

    @property
    def drawpoints(self):
        """list: geomutils.Pt2D objects that can be used to trace the curve in a visual display.
        """

        return [Pt2D(0.0, self(0.0))] + self.anchorpoints + [Pt2D(1.0, self(1.0))]

    def construct_multiple(self, count, overlap, midpoint_to_edge):
        """Construct multiple copies of this FuzzyCurve, distributing based on the method arguments.

        Args:
            count (int): The number of curves to produce; minimum of 2.
            overlap (float): Rough percentage of overlap between curves; in the range of [0,1].
            midpoint_to_edge (boolean): If true, the first and last curves will have their midpoints shifted to either
                                      edge of the graph space, with additional curves spaced appropriately.

        Raises:
            ValueError: If `count` is less than 2.

        """
        if count < 2:
            raise ValueError('At least two curves must be requested')

        basestep = 1.0 / count
        startx = basestep / 2
        if midpoint_to_edge:
            basestep = 1.0 / (count - 1)
            startx = 0.0

        lowerwidth = basestep + (basestep * overlap * 2)
        widthratio = lowerwidth / self.lowspread
        upperwidth = self.highspread * widthratio

        ret = []
        for i in range(count):
            dup = copy.deepcopy(self)
            currmid = startx + (basestep * i)

            dup.xmidpoint = currmid
            dup.lowspread = lowerwidth
            dup.highspread = upperwidth
            ret.append(dup)

        return ret


#######################################################################

class StepCurve(FuzzyCurve):
    """A curve with a discrete-step shape.

    Attributes:
        name (str): The name associated with the curve.
        yleft (float): Height of the left end of the steps.
        yright (float): Height of the right end of the steps.
        xMin (float): Where the steps begin along the x-axis.
        xMax (float): Where the steps end along the x-axis.

        monotonic (boolean): **Class attribute**; specifies if the curve is monotonic when processed.

    Args:
        name (str): The name to assign to the curve.

        """
    monotonic = True

    def __init__(self, name):
        FuzzyCurve.__init__(self, name)

        self._steps = 2
        self.yleft = 0.0
        self.yright = 1.0
        self.xMin = 0.0
        self.xMax = 1.0

    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """

        if inval <= self.xMin:
            return self.yleft
        if inval > self.xMax:
            return self.yright
        x_incr = (self.xMax - self.xMin) / self._steps
        y_incr = (self.yright - self.yleft) / (self._steps - 1)

        y_ind = floor(inval / x_incr)

        return y_ind * y_incr + self.yleft

    @property
    def steps(self):
        """int: The number of steps to include in the curve."""
        return self._steps

    @steps.setter
    def steps(self, st):

        self._steps = int(st)

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """

        x_incr = (self.xMax - self.xMin) / self._steps
        y = self.yleft
        y_incr = (self.yright - self.yleft) / (self._steps - 1)

        outlist = []
        for i in range(self._steps):
            x = i * x_incr + self.xMin
            outlist.append(Pt2D(x, y))
            outlist.append(Pt2D(x + x_incr, y))
            y += y_incr
        return outlist

    @property
    def drawpoints(self):
        """list: geomutils.Pt2D objects that can be used to trace the curve in a visual display.
        """

        return [Pt2D(0.0, self(0.0))] + self.anchorpoints + [Pt2D(1.0, self(1.0))]

    def construct_multiple(self, count, overlap, midpoint_to_edge):

        if count < 2:
            raise ValueError('At least two curves must be requested')

        basestep = 1.0 / count
        startx = basestep / 2
        if midpoint_to_edge:
            basestep = 1.0 / (count - 1)
            startx = 0.0

        hext = basestep / 2 + (basestep * overlap * 2)

        ret = []
        for i in range(count):
            dup = copy.deepcopy(self)
            currmid = startx + (basestep * i)

            dup.xMin = currmid - hext
            dup.xMax = currmid + hext
            ret.append(dup)

        return ret


#######################################################################
class PolynomialCurve(FuzzyCurve):
    """A curve that conforms to the equation: :math:`f(x) = ax^2+bx+c`.

    Attributes:
        name (str): The name associated with the curve.
        monotonic (boolean): **Class attribute**; specifies if the curve is monotonic when processed.


    Args:
        name (str): The name to assign to the curve.

    """

    def __init__(self, name):
        FuzzyCurve.__init__(self, name)

        self.a = 1.
        self.b = -1.
        self.c = 0.25
        self._xmid = 0

    def __repr__(self):
        return "a={0}, b={1}, c={2}".format(self.a, self.b, self.c)

    def __str__(self):
        return self.__repr__()

    @property
    def xmidpoint(self):
        """float: midpoint along x-axis."""
        return self._xmid + 0.5

    @xmidpoint.setter
    def xmidpoint(self, xm):
        self._xmid = xm - 0.5

    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """
        xval = inval - self._xmid
        return (self.a * xval**2) + (self.b * xval) + self.c

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """

        inflx = -self.b / (self.a * 2) if self.a != 0. else 0.5
        return [Pt2D(0.0, self(0.0)), Pt2D(inflx, self(inflx)), Pt2D(1.0, self(1.0))]

    def construct_multiple(self, count, overlap, midpoint_to_edge):
        """Construct multiple copies of this FuzzyCurve, distributing based on the method arguments.

        Args:
            count (int): The number of curves to produce; minimum of 2.
            overlap (float): Not used.
            midpoint_to_edge (boolean): If true, the first and last curves will have their midpoints shifted to either
                                      edge of the graph space, with additional curves spaced appropriately.

        Raises:
            ValueError: If `count` is less than 2.

        """
        if count < 2:
            raise ValueError('At least two curves must be requested')

        basestep = 1.0 / count
        startx = basestep / 2
        if midpoint_to_edge:
            basestep = 1.0 / (count - 1)
            startx = 0.0

        ret = []
        for i in range(count):
            dup = copy.deepcopy(self)

            currmid = startx + (basestep * i)

            dup.xmidpoint = currmid
            ret.append(dup)

        return ret

    def multiple_allow_overlap(self):
        """Flag indicating whether or not multiple instances can overlap when templated.

        Returns:
            bool: True if overlapping is allowed; False otherwise.
        """

        return False


#######################################################################
class CubicCurve(FuzzyCurve):
    """A curve that conforms to the equation: :math:`f(x)=ax^3+bx^2+cx+d.`

    Attributes:
        name (str): The name associated with the curve.
        monotonic (boolean): **Class attribute**; specifies if the curve is monotonic when processed.


    Args:
        name (str): The name to assign to the curve.

    """

    def __init__(self, name):
        FuzzyCurve.__init__(self, name)

        self.a = 1.
        self.b = -1.5
        self.c = 0.5
        self.d = 0.15
        self._xmid = 0

    def __repr__(self):
        return "a={0}, b={1}, c={2}, d={3}".format(self.a, self.b, self.c, self.d)

    def __str__(self):
        return self.__repr__()

    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """
        xval = inval - self._xmid
        return (self.a * xval**3) + (self.b * xval**2) + (self.c * xval) + self.d

    @property
    def xmidpoint(self):
        """float: midpoint along x-axis."""
        return self._xmid+0.5

    @xmidpoint.setter
    def xmidpoint(self, xm):
        self._xmid = xm - 0.5

    @property
    def ctrlpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """
        delta0 = self.b**2 - (3 * self.a * self.c)
        if delta0 > 0:
            delta0 **= 0.5
            lnflx1 = (-self.b + delta0) / (3 * self.a)
            lnflx2 = (-self.b - delta0) / (3 * self.a)
            return [Pt2D(lnflx1, self(lnflx1)), Pt2D(lnflx2, self(lnflx2))]
        return []

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """

        inflx = -self.b / (self.a * 3) if self.a != 0. else 0.5
        return [Pt2D(0.0, self(0.0)), Pt2D(inflx, self(inflx)), Pt2D(1.0, self(1.0))]

    def construct_multiple(self, count, overlap, midpoint_to_edge):
        """Construct multiple copies of this FuzzyCurve, distributing based on the method arguments.

        Args:
            count (int): The number of curves to produce; minimum of 2.
            overlap (float): Not used.
            midpoint_to_edge (boolean): If true, the first and last curves will have their midpoints shifted to either
                                      edge of the graph space, with additional curves spaced appropriately.

        Raises:
            ValueError: If `count` is less than 2.

        """
        if count < 2:
            raise ValueError('At least two curves must be requested')

        basestep = 1.0 / count
        startx = basestep / 2
        if midpoint_to_edge:
            basestep = 1.0 / (count - 1)
            startx = 0.0

        ret = []
        for i in range(count):
            dup = copy.deepcopy(self)

            currmid = startx + (basestep * i)

            dup.xmidpoint = currmid
            ret.append(dup)

        return ret

    def multiple_allow_overlap(self):
        """Flag indicating whether or not multiple instances can overlap when templated.

        Returns:
            bool: True if overlapping is allowed; False otherwise.
        """

        return False
#######################################################################


class PiecewiseCurve(FuzzyCurve):
    """A curve used to represent a membership function, result function, or implication.

    A curve is composed of segments, which themselves are represented as math functions. Curves
    are used when choosing values in response to inputs, and for representing the final volume
    for combined implications.

    Attributes:
        name (str): The name associated with the curve.

    Args:
        name (str): The name to assign to the curve.
        segments (list,optional): List of segments. If omitted, will be initialized with a single
          linear segment from (0.0,0.0) to (1.0,0.0).

    """

    def __init__(self, name, segments=None):
        FuzzyCurve.__init__(self, name)
        if segments is None:
            segments = []

        self._segments = segments
        if len(self._segments) == 0:
            # initialize with a single linear segment
            self._segments.append(LinearSegment(Pt2D(0.0, 0.0), Pt2D(1.0, 0.0)))

    def __repr__(self):
        return '{0}: {1}'.format(self.name, ','.join([s.__repr__() for s in self._segments]))

    def __call__(self, inval):
        """Given an x-value, retrieves the appropriate Y-value.

        Args:
            inval (float): The value to use for the query.

        Returns:
            float: The y-equivalent for inVal as a float.

        Raises:
            ValueError: If inValue is less than 0 or greater than 1.
        """

        # check range
        inval = bounds_check(inval)

        for s in self._segments:
            if s.x_inrange(inval):
                return s(inval)

        # we should never get here, but who knows...
        return None

    def copy_segments(self):
        """Create a discrete copy of the segments that compose the curve.

        Returns:
            list: An explicit copy of all internal segments.
        """
        return copy.deepcopy(list(self._segments))

    def overwrite_segments(self, segs):
        """Replace the curve segments with an explicit copy of the supplied segments.

        Args:
            segs (list): The segments to copy and use.
        """
        self._segments = copy.deepcopy(tuple(segs))

    def segments(self):
        """Iterator for internal segments

        Yields:
            BaseSegment: The next segment in the curve
        """
        for s in self._segments:
            yield s

    @staticmethod
    def _ensure_end_to_end(segs):
        """Makes sure that all endpoints of the segments overlap, and that the entire x-range is [0,1]

        Args:
            segs (list): Segments to be processed; on return, x endpoints will have been adjusted to
              properly overlap.
        """

        if len(segs) > 0:

            for i in range(1, len(segs)):
                # use absolute equality here
                if segs[i].leftpoint.x != segs[i - 1].rightpoint.x:
                    segs[i].leftpoint = Pt2D(segs[i - 1].rightpoint.x, segs[i](segs[i - 1].rightpoint.x))

            # ensure [0,1]
            segs[0].leftpoint = Pt2D(0.0, segs[0](0.0))
            segs[-1].rightpoint = Pt2D(1.0, segs[-1](1.0))

    @property
    def anchorpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """
        if self._segments is None:
            return []
        pts = [s.leftpoint for s in self._segments]
        pts.append(self._segments[-1].rightpoint)
        return pts

    @property
    def ctrlpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve.
        """
        pts = []
        for s in self._segments:
            pts += s.ctrlpoints
        return pts

    @property
    def drawpoints(self):
        """list: geomutils.Pt2D objects that can be used to trace the curve in a visual display.
        """
        allpoints = []

        for s in self._segments:
            allpoints += s.drawpoints
        return allpoints

    def construct_multiple(self, count, overlap, midpoint_to_edge):
        """This method is not supported by this subclass, but is included as a safetycheck

        Args:
            count (int): Not used.
            overlap (float): Not used.
            midpoint_to_edge (boolean): Not used.

        Raises:
            NotImplementedError: On call.

        """
        raise NotImplementedError(self.__name__ + ' does not support construct_multiple method.')


#######################################################################

class FieldEntry(object):
    """Description of how to represent a particular FuzzyCurve attribute/property using a user interface widget
        (typically a spinner).
    
    Attributes:
        label (str): The dlg_label to display for the property in the UI.
        prop (str): The actual property/attribute being represented.
        min (float or int): The minimum allowed value.
        max (float or int): The maximum allowed value.
        valType (str): Pattern denoting type of value represented; currently only `'i'` (int) and `'f'` (float) are
                       supported.
        zeroAllow (bool): Flag indicating whether or not zero is a valid value for the represented property.
        lowerProp (str): The property of the object that restricts the lower boundary of values.
        upperProp (str): The property of the object that restricts the upper boundary of values.
        isX (bool): Flag indicating whether or not this property/attribute represents a value along the x-axis. If so,
                    it may be subject to transformation in the view model.
        stepSize (float or int): Increment to apply to property when represented in spinner widget.
    
    Args:
        lbl (str): The dlg_label to display for the property in the UI.
        key (str): The actual property/attribute being represented.
        min (float or int, optional): The minimum allowed value; defaults to negative infinity.
        max (float or int, optional): The maximum allowed value; defaults to positive infinity.
        
    Keyword Args:
        valType (str, optional): Pattern denoting type of value represented; either `'i'` (int) or `'f'` (float);
                                 defaults to `'f'`
        zeroAllow (bool, optional): Flag indicating whether or not zero is a valid value; defaults to `True`.
        lowerProp (str, optional): The property of the object that restricts the lower boundary of values; default is
                                   `None`.
        upperProp (str, optional): The property of the object that restricts the upper boundary of values; default is
                                   `None`.
        isX (bool, optional): Flag indicating whether or not this property/attribute represents a value along the
                              x-axis; defaults to `False`
        stepSize (float or int, optional): Increment to apply to property when represented in spinner widget; defaults
                                           to `None`.
    """

    def __init__(self, lbl, key, min=-inf, max=inf, **kwargs):
        self.label = lbl
        self.prop = key
        self.min = min
        self.max = max

        self.valType = kwargs.get("valType", 'f')
        self.zeroAllowed = kwargs.get("zeroAllowed", True)
        self.lowerProp = kwargs.get("lowerProp", None)
        self.upperProp = kwargs.get("upperProp", None)
        self.isX = kwargs.get("isX", False)
        self.stepSize = kwargs.get("stepSize", None)


#######################################################################


_curveTemplates = {"Linear": LinearCurve,
                   "Polynomial": PolynomialCurve,
                   "Cubic": CubicCurve,
                   "Gaussian": GaussianCurve,
                   "Sigmoidal": SigmoidCurve,
                   "Triangular": TriangleCurve,
                   "Trapezoidal": TrapezoidCurve,
                   "Step": StepCurve,
                   "Custom": PiecewiseCurve}

# Each property below provides a dlg_label and a property name.
# Additional arguments are for describing the widget used to
# manipulate the value from within the table.
_allProperties = (
                  # FieldEntry("X-Left", "xleft", upperProp="xright", isX=True),
                  # FieldEntry("X-Right", "xright", lowerProp="xleft", isX=True),
                  # FieldEntry("X-Minimum", "xMin", upperProp="xMax", isX=True),
                  # FieldEntry("X-Maximum", "xMax", lowerProp="xMin", isX=True),
                  FieldEntry("Y-Left", "yleft", 0.0, 1.0),
                  FieldEntry("Y-Right", "yright", 0.0, 1.0),
                  FieldEntry("Y-Minimum", "ymin", 0.0, 1.0),
                  FieldEntry("Y-Maximum", "ymax", 0.0, 1.0),
                  FieldEntry("X-Midpoint", "xmidpoint", isX=True),
                  FieldEntry("Spread", "spread"),
                  FieldEntry("Lower Width", "lowspread", 0.0, 1.0, lowerProp="highspread", zeroAllowed=False),
                  FieldEntry("Upper Width", "highspread", 0.0, 1.0, upperProp="lowspread", zeroAllowed=False),
                  FieldEntry("Slope", "slope", zeroAllowed=False, stepSize=1),
                  FieldEntry("Steps", "steps", 2, 20, zeroAllowed=False, valType='i'),
                  FieldEntry("A", "a"),
                  FieldEntry("B", "b"),
                  FieldEntry("C", "c"),
                  FieldEntry("D", "d"))


def get_curvelist():
    """Retrieve a list of curve types defined in the module.

    Returns:
        list: List of string of curve titles to use in menus
    """
    return list(_curveTemplates.keys())


def get_curve_typenames():
    """Retrieve a list of types for all curves other than piecewise.

    Returns:
        list: List of strings of class names.
    """
    return [x.__name__ for x in _curveTemplates.values()]


def get_curvetype_for_name(name):
    """ Retrieve class identifier for a provided name

    Args:
        name (str): The name of the string to return.

    Returns:
        type: The type of the curve class object.
    """

    return _curveTemplates[name]


if sys.version_info[0] != 3:
    def _dict_iteritems2(d): return d.iteritems()
    dict_iteritems = _dict_iteritems2
else:
    def _dict_iteritems3(d): return d.items()
    dict_iteritems = _dict_iteritems3


def get_curvename_for_type(classtype):
    """Get the common-name identifier for the name of a FuzzyCurve subclass.

    Args:
        classtype (type): The object type identifier to query.

    Returns:
        str: The name of the supplied classType.

    Raises:
        ValueError: If type does not have a corresponding name.
    """

    for k, v in dict_iteritems(_curveTemplates):
        if v == classtype:
            return k

    raise ValueError("No matching value")


def get_propdetails_for_obj(o):
    """Retrieve all supported entry attributes.

    Args:
        o (object): The object to query for curve-related attributes

    Returns:
        list: A collection of `FieldEntry` values that match attributes supported by the queried object.
    """

    selected = []
    for entry in _allProperties:
        if hasattr(o, entry.prop):
            selected.append(entry)

    return selected
