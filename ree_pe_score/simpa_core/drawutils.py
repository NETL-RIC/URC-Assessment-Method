"""Module for miscallaneous drawing utilities.

External Dependencies:
    * `numpy <http://www.numpy.org/>`_
"""

import numpy as np
import sys


class SimpaColor(object):
    """Represents a color record.

    The default implementation assumes 1 byte channel size with r,g,b,a color channels.

    Attributes:
        r (int): The red color channel value in the range of [0,255].
        g (int): The green color channel value in the range of [0,255].
        b (int): The blue color channel value in the range of [0,255].
        a (int): The alpha color channel value in the range of [0,255].

    Args:
        r (int, optional): The initial red color channel value in the range of [0,255].
        g (int, optional): The initial green color channel value in the range of [0,255].
        b (int, optional): The initial blue color channel value in the range of [0,255].
        a (int, optional): The initial alpha color channel value in the range of [0,255].

    Keyword Args:
        argb (list): Alternative initialization scheme with a list of ints with the channels in the
          order of a,r,g,b.
    """

    def __init__(self, r=0, g=0, b=0, a=255, **kwargs):

        self.r = r
        self.g = g
        self.b = b
        self.a = a

        # assign colors based on different formats
        if 'argb' in kwargs:
            self.a, self.r, self.g, self.b = kwargs['argb']

    def __str__(self):
        return "red: {0}, green: {1}, blue: {2}, alpha: {3}".format(self.r, self.g, self.b, self.a)

    def __iter__(self):
        yield self.r
        yield self.g
        yield self.b
        yield self.a

    @property
    def uint32_argb(self):
        """numpy.uint32: ARGB representation of the color packed into a single 32-bit unsigned int."""

        argb = np.uint32(self.b) + (np.uint32(self.g) << 8) + (np.uint32(self.r) << 16) + (np.uint32(self.a) << 24)

        return argb


def mix_colors(color1, color2, balance):
    """Mix two QColors.

    Args:
        color1 (SimpaColor): The first color to mix.
        color2 (SimpaColor): The second color to mix.
        balance (float): Mixing value in the range of [0-1].

    Returns:
        SimpaColor: The result of the two blended colors.
    """

    r = int(color1.r * balance + color2.r * (1. - balance))
    g = int(color1.g * balance + color2.g * (1. - balance))
    b = int(color1.b * balance + color2.b * (1. - balance))
    a = int(color1.a * balance + color2.a * (1. - balance))

    return SimpaColor(r, g, b, a)
