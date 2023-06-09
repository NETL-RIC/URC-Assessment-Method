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

"""Miscallaneous functions for mapping color data between Qt and OpenGL."""
from ._compat import QColor

from .._support import GradientRecord
import glm

def vecToQColor(c):
    """Converts from glm.vec3 or glm.vec4 to QColor.

    Args:
        c (glm.vec3 or glm.vec4): The color vector to convert.

    Returns:
        PyQt5.QtGui.QColor: The Qt representation of the color.
    """

    return QColor.fromRgbF(c[0],c[1],c[2],c[3])

def QColorToVec(c):
    """Converts from QColor to glm.vec4.

    Args:
        c (PyQt5.QtGui.QColor): The QColor object to convert.

    Returns:
        glm.vec4: The color in a representation that OpenGL can understand.
    """

    return glm.vec4(c.redF(),c.greenF(),c.blueF(),c.alphaF())

def GradRecToStops(gr):
    """Convert a GradientRecord to stops that QLinearGradient can understand.

    Args:
        gr (GradientRecord): The gradient record to convert.

    Returns:
        list: tuple entries of the form (weight,PyQt5.QtGui.QColor) which can be fed to a
              PyQt5.QWidgets.QLinearGradient object.
    """

    return [(wt,vecToQColor(color)) for wt,color in gr]

def StopsToGradRec(stps):
    """Convert a list of stops into a GradientRecord object.

    Args:
        stps (list): tuple entries of the form (weight,PyQt5.QtGui.QColor), typically retrieved from a
                     PyQt5.QWidgets.QLinearGradient object.

    Returns:
        GradientRecord: The gradient stop representation.
    """

    ret = GradientRecord()
    for wt,color in stps:
        ret.addColorAnchor(wt,QColorToVec(color))
    return ret
