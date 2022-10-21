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