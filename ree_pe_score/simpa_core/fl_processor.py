"""Methods and classes used for processing FuzzyLogic objects in non-standard ways.

External Dependencies:
    * `numpy <http://www.numpy.org/>`_
"""

from ..fuzzylogic import fuzzycurves as fc
from ..fuzzylogic.geomutils import Pt2D, bounds_check
from .containers import SimpaException
import numpy as np


class NPFuzzyCurve(fc.FuzzyCurve):
    """Static representation of a fuzzy curve, which acts as a lookup table.

    This will be useful for speeding up processing.

    Args:
        name (str): The name of the curve.
        nparr (numpy.ndarrya): A numpy 1D-array of y-values of the curve.
    """

    def __init__(self, name, nparr):

        fc.FuzzyCurve.__init__(self, name)

        if len(nparr.shape) > 1:
            raise SimpaException("numpy.array must be one-dimensional.")
        if len(nparr) <= 1:
            raise SimpaException("numpy.array must have at least two values.")
        del self._segments
        self._yVals = nparr
        self._xStep = 1.0 / (len(nparr) - 1)

    def __repr__(self):
        return '(0,{0}),...,(1,{1})'.format(self._yVals[0], self._yVals[-1])

    def __call__(self, inval):

        inval = bounds_check(inval)
        lowind = inval // (len(self._yVals) - 1)
        highind = lowind + 1

        lowx = lowind * self._xStep
        highx = highind * self._xStep

        # if matches lower index, return
        if lowind >= 0 and lowx == inval:
            return self._yVals[lowind]

        # if matches upper index, return
        if highind < len(self._yVals) and highx == inval:
            return self._yVals[highind]

        # if we get here, perform linear interpolation
        i = (inval - lowx) / (highx - lowx)
        dist = self._yVals[highind] - self._yVals[lowind]
        return self._yVals[lowind] + (dist * i)

    def copy_segments(self):
        """Not implemented; utilized as a safety check.

        Raises:
            RuntimeError: On call.
        """

        raise RuntimeError("copy_segments not implemented.")

    def overwrite_segments(self, segs):
        """Not implemented; utilized as a safety check.

        Raises:
            RuntimeError: On call.
        """
        raise RuntimeError("overwrite_segments not implemented.")

    @property
    def ctrlpoints(self):
        """list: geomutils.Pt2D objects representing the control points of the curve."""
        return [Pt2D(0.0, self._yVals[0]), Pt2D(1.0, self._yVals[-1])]

    @property
    def drawpoints(self):
        """ list: Enough points to draw the segment."""
        return [Pt2D(self._xStep * i, yval) for i,yval in enumerate(self._yVals)]


#######################################################################

# ... add Processing stuff

#######################################################################
def flcurve_to_npcurve(incurve, samples):
    """Create an NPFuzzyCurve from a standard FuzzyCurve.

    Args:
        incurve (components.fuzzylogic.FuzzyCurve): The curve to generate a new NPCurve from.
        samples (int): The number of y-samples to include in the new NPFuzzyCurve.

    Returns:
        NPFuzzyCurve: Based on the value passed with inCurve.
    """

    vals = np.zeros(shape=[samples])

    step = 1. / (samples - 1)

    for i in range(samples):
        vals[i] = incurve(step * i)

    return NPFuzzyCurve(incurve.name, vals)
