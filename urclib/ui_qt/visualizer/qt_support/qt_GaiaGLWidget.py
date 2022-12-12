"""Widget for embedding the geometry scene logic within a Qt-based GUI."""

import glm
import numpy as np
from OpenGL.error import GLError
from PyQt5.Qt import QCursor, QSurfaceFormat
from PyQt5.QtCore import Qt, pyqtSignal,pyqtSlot,QTimer
from PyQt5.QtWidgets import QOpenGLWidget

from ..geometryglscene import GeometryGLScene, GaiaGLShaderException


class GaiaQtGLWidget(QOpenGLWidget):
    """Qt-compatible widget for visualization support.

    Attributes:
        GLDrawErrHandler (function(str,str),optional): Optional function that takes a title and message as arguments.
           This function is called when an OpenGL error is encountered.
        dragButton (int): Qt enumeration for which mouse button is used with drag operations. Default is `Qt.LeftButton`.
        selectButton (int): Qt enumeration for which mouse button is used with selection operations. Default is
            `Qt.RightButton`.
        rubberBandEnabled (bool): Flag indicating whether or not to allow rubber-band drawing for operations.
            Defaults to `True`.
        initZoom (list or number,optional): Either List of extents or id of layer to zoom to on load of scene data. Default is `None`.

    Qt Signals:
        selectionpicked (int,int): Emitted when a geometric object in the scene is selected by the user. Emits the
            layer id and geometry object's index within that layer.
        mouseMoved (float,float): Emitted whenever the mouse is moved within the widget. Mouse tracking must be enabled
            for this to work properly. The (x,y) coordinate emitted is in scene/world space.
        mouseInOut (bool): Emitted when the mouse cursor enters or leaves the scene. Flag is emitted indicating whether
           or not the cursor is still in the scene.

    Arguments:
        parent (QWidget,optional): The parent widget. Defaults to `None`.
        inScene (GeometryGLScene,optional): The scene object to associate with the widget; defaults to `None`.
    """

    selectionpicked = pyqtSignal(int, int, )
    mouseMoved = pyqtSignal(float,float)
    mouseInOut = pyqtSignal(bool)

    class SimpleExtent(object):
        """Simple representation of rectangular extents. Generic representation of `QRect` object.

        Attributes:
            width (float): width of the extent.
            height (float): height of the extent.
            x (float): The x-component of the bottom-left origin.
            y (float): The y-component of the bottom-left origin.

        Args:
            qSize (QRect): Rect to convert into extents.
        """

        def __init__(self,qSize):

            self.width = qSize.width()
            self.height = qSize.height()
            self.x = qSize.x()
            self.y = qSize.y()

        @property
        def list_extents(self):
            """list: extents in [left,right,bottom,top] form."""
            return [self.x,self.x+self.width,self.y,self.y+self.height]

    def __init__(self, parent=None, inScene=None):

        QOpenGLWidget.__init__(self,parent)

        frmt = QSurfaceFormat()

        frmt.setDepthBufferSize(24)
        frmt.setStencilBufferSize(1)
        frmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        frmt.setProfile(QSurfaceFormat.CoreProfile)
        frmt.setRenderableType(QSurfaceFormat.OpenGL)
        # stick with 4.3 for compatibility with old drivers, but bump only when needed.
        frmt.setVersion(4, 3)
        self.setFormat(frmt)

        self.GLDrawErrHandler=None

        self._scene = None
        if isinstance(inScene, GeometryGLScene):
            self.scene = inScene
        self._dragAnchor = None

        self.dragButton = Qt.LeftButton
        self.selectButton = Qt.RightButton
        self.rubberBandEnabled = True
        self.initZoom = None

    def cleanupGL(self):
        """Deallocate any referenced OpenGL resources.
        """
        if self._scene is not None:
            self._scene.cleanupOpenGL()


    @property
    def scene(self):
        """GeometryGLScene: Teh currently assigned scene object"""
        return self._scene

    @scene.setter
    def scene(self,s):
        self._scene=s

        # hook in widget specific behavior into scene object
        self._scene.widget=self
        self._scene.refreshkey = 'update'
        self._scene.extentkey = 'getSimpleExtent'
        self._scene.beginContextKey = 'makeCurrent'
        self._scene.endContextKey = 'doneCurrent'
        self._contextRefCount = 0

        if self.isValid():
            self.makeCurrent()
            self.initializeGL()
            self.doneCurrent()
            self.update()

    def getSimpleExtent(self):
        """ Retrieve scene extent in pixel space.

        Returns:
            GaiaGLWidget.GaiaQtGLWidget: Generalized extent object for widget.
        """
        return self.__class__.SimpleExtent(self.rect())


    # <editor-fold desc="QOpenGLWidget overrides">
    def paintGL(self):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qopenglwidget.html#paintGL)
        """

        if self._scene is not None:

            try:
                self._scene.paintGL()
            except GLError as err:
                if self.GLDrawErrHandler is not None:
                    self.GLDrawErrHandler("Drawing error", 'Error during draw: {}'.format(err))
                else:
                    raise

        QOpenGLWidget.paintGL(self)

    def initializeGL(self):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qopenglwidget.html#initializeGL)
        """

        if self._scene is None:
            QOpenGLWidget.initializeGL(self)
            return
        try:
            self._scene.initializeGL()
            size = self._scene.GetGLExtents()
            self.resize(size.width, size.height)

        except GLError as err:
            if self.GLDrawErrHandler is not None:
                self.GLDrawErrHandler("initGL error", 'Error during initGL: {}'.format(err))
            else:
                raise
        except GaiaGLShaderException as err:
            self.GLDrawErrHandler(err.msg,err.log)
        QOpenGLWidget.initializeGL(self)


    def resizeGL(self, w, h):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        Args:
            w (int): The new width of the viewport, in pixels.
            h (int): The new height of the viewport, in pixels.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qopenglwidget.html#resizeGL)
        """

        if self._scene is None:
            self._raiseUninitException('resizeGL')
        self._scene.resizeGL(w, h)

        QOpenGLWidget.resizeGL(self,w,h)

    def makeCurrent(self):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qopenglwidget.html#makeCurrent)
        """

        if  self.context() is not None and \
                self.context()!=self.context().currentContext():
            QOpenGLWidget.makeCurrent(self)
            self._contextRefCount+=1

    def doneCurrent(self):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qopenglwidget.html#doneCurrent)
        """

        if self._contextRefCount>0:
            self._contextRefCount-=1
            if self._contextRefCount==0:
                QOpenGLWidget.doneCurrent(self)
    # </editor-fold>

    def _raiseUninitException(self,fnlbl):
        """ Convenience method for raising an error when method is called which relies on `scene` property, when
        `scene` is `None`

        Args:
            fnlbl (str): The name of the function/method being invoked.
        """
        raise ValueError("Scene is 'None'. Set _scene attribute before calling {}().".format(fnlbl))

    def pointToScene(self,curPos,toClipspace=False):
        """Converts a point (generally considered the cursor position) from pixel space to projected space.

        Args:
            curPos (glm.vec2): The point in widget pixel space.
            toClipspace (bool,optional): If true, converts coordinate into clip space instead of world space. Defaults
              to `False`.

        Returns:
            glm.vec4: The coordinates in scene projected space.

        """
        bRect = self._scene.GetGLExtents()
        bSize = glm.vec2(float(bRect.width), float(bRect.height))
        normPos = (bSize-curPos) / bSize

        curPos = (2 * normPos) - glm.vec2(1.)
        curPos.x *= -1.
        # print(curPos)
        if not toClipspace:
            curPos=self._scene.ClipPtToScene(curPos).xy



        return glm.vec4(curPos, 0., 0.)

    def forceRefresh(self):
        """Explicitly mark the scene for redrawing and post an update notification."""
        if self._scene is not None:
            self._scene.markFullRefresh()
            self.update()

    # <editor-fold desc="interaction stuff">

    def mouseMoveEvent(self, event):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        Args:
            event (PyQt5.QtGui.QMouseEvent): The triggering event.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qwidget.html#mouseMoveEvent)
        """

        curPos = self.pointToScene(glm.vec2(float(event.x()), float(event.y())))

        if event.buttons() & (self.dragButton | self.selectButton):
            if self._dragAnchor is not None:
                #translate

                if event.buttons() & self.dragButton:
                    start = self.pointToScene(glm.vec2(float(self._dragAnchor.x()), float(self._dragAnchor.y())))

                    self._scene.DistanceForTranslate(start,curPos)
                    self._dragAnchor = event.pos()
                elif self.rubberBandEnabled and event.buttons() & self.selectButton:
                    nCurPos = self.pointToScene(glm.vec2(float(event.x()), float(event.y())),True)
                    start = self.pointToScene(glm.vec2(float(self._dragAnchor.x()), float(self._dragAnchor.y())),True)
                    self._scene.drawRubberBand = True
                    self._scene.updateRubberBand(start,nCurPos)
                    self.update()
            else:
                self._dragAnchor = event.pos()

        self.mouseMoved.emit(*curPos.xy)


    def mouseReleaseEvent(self, event):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        Args:
            event (PyQt5.QtGui.QMouseEvent): The triggering event.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qwidget.html#mouseReleaseEvent)
        """

        if self._dragAnchor is not None and event.button() == self.selectButton:
            self._scene.drawRubberBand=False

            # Todo: work out kinks in centering on box zoom
            # find aspect ratio of screen
            bwidth = abs(self._dragAnchor.x()-event.pos().x())
            bheight = abs(self._dragAnchor.y() - event.pos().y())
            center = np.array([(self._dragAnchor.x() + event.pos().x()) / 2,
                               (self._dragAnchor.y() + event.pos().y()) / 2,
                               0., ], dtype=np.float32)

            self._dragAnchor=None
            if bwidth > 0 and bheight > 0:

                self._scene.zoomToRubberBand()

            return

        if self._scene.allowPicking and event.button() == self.selectButton:

            try:
                # bRect = self.rect()
                # nx = (event.x() - bRect.left())/bRect.width()
                # ny = 1.0 - ((event.y()-bRect.top())/bRect.height())f
                # pId = self._scene.doMousePick(nx,ny)
                pos = self.mapFromGlobal(QCursor.pos())
                pId = self._scene.doMousePick(pos.x(), pos.y())
                if pId is not None:
                    self._scene.ToggleLayerSelect(*pId)

                    self.selectionpicked.emit(*pId)
                self.update()
            except GLError as err:
                if self.GLDrawErrHandler is not None:
                    self.GLDrawErrHandler("Picking error", 'Error during pick: {}'.format(err))
                else:
                    raise

        self._dragAnchor=None

    def enterEvent(self,event):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        Args:
            event (PyQt5.QtGui.QEvent): The triggering event.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qwidget.html#enterEvent)
        """

        self.mouseInOut.emit(True)

    def leaveEvent(self,event):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        Args:
            event (PyQt5.QtGui.QEvent): The triggering event.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qwidget.html#leaveEvent)
        """

        self.mouseInOut.emit(False)

    def wheelEvent(self,event):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        Args:
            event (PyQt5.QtGui.QWheelEvent): The triggering event.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qwidget.html#wheelEvent)
        """
        # do zoom
        step = 0.5

        if event.modifiers() & Qt.ShiftModifier:
            # modify scroll wheel stepsize:
            # 50% if control is held
            # 25% if shift+control is held
            step = 0.125 if event.modifiers() & Qt.ControlModifier else 0.25
        self._scene.IncrementZoom(event.angleDelta().y() > 0, step)

    def showEvent(self, event):
        """This is an overload of a method of `QOpenGLWidget`. See official documentation for more information.

        Args:
            event (PyQt5.QtGui.QShowEvent): The triggering event.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qwidget.html#showEvent)
        """

        super().showEvent(event)
        # use timer to apply after all show-setup stuff is completed
        if self.initZoom is not None:
            QTimer.singleShot(0, self._doInitLayerZoom)

    @pyqtSlot()
    def _doInitLayerZoom(self):
        """Perform scene zoom on load."""
        # Apply initial zoom extent if present
        if isinstance(self.initZoom,int):
            self._scene.zoomToLayer(self.initZoom)
        else:
            self._scene.zoomToExts(*self.initZoom,True)
        self.initZoom=None
    # </editor-fold>
