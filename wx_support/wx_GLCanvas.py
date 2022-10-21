"""Widget for embedding geometry scene in wx GUI."""
from __future__ import print_function, absolute_import, division, unicode_literals

from ..geometryglscene import GeometryGLScene
from ..ogrglscene import OGRGLScene

try:
    import wx
    from wx import glcanvas
except ImportError:
    raise ImportError("Required dependency wx.glcanvas not present")

try:
    from OpenGL.GL import *

except ImportError:
    raise ImportError("Required dependency OpenGL not present")


class _CommonGLCanvas(glcanvas.GLCanvas):
    # https://stackoverflow.com/questions/6031870/adding-wxglcanvas-to-wxpanel-problem
    def __init__(self, *args, **kwargs):

        attribList = (glcanvas.WX_GL_RGBA,  # RGBA
                      glcanvas.WX_GL_DOUBLEBUFFER,  # Double Buffered
                      glcanvas.WX_GL_DEPTH_SIZE, 24,  # 24 bit
                      glcanvas.WX_GL_STENCIL_SIZE, 1,  # 1-bit
                      glcanvas.WX_GL_CORE_PROFILE,     # Use OpenGL style introduces in 3.2
                      glcanvas.WX_GL_MAJOR_VERSION, 4, # Use OpenGL 4
                      glcanvas.WX_GL_MINOR_VERSION, 1, # Use OpenGL 4.1
                      )

        kwargs['attribList'] = attribList

        glcanvas.GLCanvas.__init__(self, *args, **kwargs)
        self.GLinitialized = False

        # Set the event handlers.
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.processEraseBackgroundEvent)
        self.Bind(wx.EVT_SIZE, self.processSizeEvent)
        self.Bind(wx.EVT_PAINT, self.processPaintEvent)

        self.context = None

    #
    # wxPython Window Handlers

    def processEraseBackgroundEvent(self, event):
        """Process the erase background event."""
        pass  # Do nothing, to avoid flashing on MSWin

    def processSizeEvent(self, event):
        """Process the resize event."""
        if self.context and self.GLinitialized:
            # Make sure the frame is shown before calling SetCurrent.
            self.Show()
            self.SetCurrent(self.context)

            size = self.GetGLExtents()
            self.resizeGL(size.width, size.height)
            self.Refresh(False)
        event.Skip()

    def makeCurrent(self):
        if self.context is not None:
            self.SetCurrent(self.context)


    def processPaintEvent(self, event):
        """Process the drawing event."""

        # This is a 'perfect' time to initialize OpenGL ... only if we need to
        if not self.GLinitialized:
            self.context = glcanvas.GLContext(self)
            self.SetCurrent(self.context)
            self.initializeGL()
            self.GLinitialized = True

            size = self.GetGLExtents()
            self.resizeGL(size.width, size.height)
            self._updateMVP()

        self.paintGL()
        self.SwapBuffers()
        event.Skip()


class GaiaOGRCanvas(_CommonGLCanvas, OGRGLScene):
    """ The wx.glcanvas.GLCanvas object is the tool for managing OpenGL context data in wx.

    This class is an example of **multiple inheritance** traits from both GLCanvas and GAIAShpScene are
    inherited and can be bound to any place where either super class is expected.

    """

    # https://stackoverflow.com/questions/6031870/adding-wxglcanvas-to-wxpanel-problem
    def __init__(self, *args, **kwargs):

        _CommonGLCanvas.__init__(self,*args, **kwargs)
        OGRGLScene.__init__(self,self,'Refresh','GetClientSize', **kwargs)
        self.beginContextKey = 'makeCurrent'
        self.Bind(wx.EVT_CLOSE, self.onCloseEvent)

    def onCloseEvent(self, *args):
        OGRGLScene.cleanupOpenGL(self)



class GaiaGeometryCanvas(_CommonGLCanvas, GeometryGLScene):
    """ The wx.glcanvas.GLCanvas object is the tool for managing OpenGL context data in wx.

    This class is an example of **multiple inheritance** traits from both GLCanvas and GAIAShpScene are
    inherited and can be bound to any place where either super class is expected.

    """

    # https://stackoverflow.com/questions/6031870/adding-wxglcanvas-to-wxpanel-problem
    def __init__(self, *args, **kwargs):
        _CommonGLCanvas.__init__(self, *args, **kwargs)
        GeometryGLScene.__init__(self, self, 'Refresh', 'GetClientSize', **kwargs)

        self.beginContextKey='makeCurrent'
        self.Bind(wx.EVT_CLOSE, self.onCloseEvent)


    def onCloseEvent(self, *args):
        GeometryGLScene.cleanupOpenGL(self)
