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

"""
2D visualizer package.
"""

from ._support import *
from ._version import VERSION as __version__

def newGeometryScene(*args,**kwargs):
    """ Initialize a new GeometryGLScene.

    Args:
        *args (list): Positional Arguments to be forwarded to constructor.
        **kwargs (dict): Keyword arguments to be forwarded to constructor.

    Returns:
        GeometryGLScene: Newly-constructed GeometryGLScene.
    """

    from .geometryglscene import GeometryGLScene
    return GeometryGLScene(*args,**kwargs)


def newOGRScene(*args,**kwargs):
    """ Initialize a new OGRGLScene.

        Args:
            *args (list): Positional Arguments to be forwarded to constructor.
            **kwargs (dict): Keyword arguments to be forwarded to constructor.

        Returns:
            OGRGLScene: Newly-constructed OGRGLScene.
        """
    from .ogrglscene import OGRGLScene
    return OGRGLScene(*args,**kwargs)

# def newStringEntry(txt,anchor,color=(0.,0.,0.,1.),h_justify="center",v_justify="center",tabspacing=4):
#     from .textrenderer import StringEntry
#     return StringEntry(txt,anchor,color,h_justify,v_justify,tabspacing)