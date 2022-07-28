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
