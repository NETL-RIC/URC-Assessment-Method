from __future__ import absolute_import, division, print_function, unicode_literals

import os

from ._support import *
from .shaders import *
from .textrenderer import TxtRenderer
from contextlib import contextmanager

POLY_GRAD_IND = IntEnum('POLY_GRAD_IND', 'VAL REF', start=0)


# def dummyFn(*args): pass
def dummyFn(): pass


# <editor-fold desc="Exception classes">
class GaiaGLException(Exception):
    pass


class GaiaGLShaderException(GaiaGLException):

    def __init__(self, msg, log):
        super().__init__(msg)
        self.msg = msg
        self.log = log
        if isinstance(self.log, bytes):
            self.log = self.log.decode('utf8')


# </editor-fold>

class GeometryGLScene(object):
    """Object for handling the rendering of geometry data and appling translation and scale transformations.

    Attributes:
        refreshkey (str): Name of function to call from `widget` whenever the draw state changes.
        extentkey (str): Name of function to call from `widget` whenever draw extents are needed.
        widget (object): The parent object that will manage the OpenGL context for the hosting UI framework.
        identMat (SimpleMat): Cached Identity Matrix.
        mdlMat   (SimpleMat): Model Matrix; transformations to be applied to objects in scene.
        viewMat (SimpleMat): View Matrix; transformations to be applied to the viewer's position.
        orthoMat (SimpleMat): Projection Matrix, using orthographic projection; describes how to render overall space.
        mvpMat (SimpleMat): Cached combination of the Model, View, and Projection matrices.
        ptVao  (GLuint): Reference to Vertex Array Object containing draw details for point geometry.
        layerStack (list): LayerRecords containing information necessary to render polygon or point layers.
        gFillVao (GLuint): Reference to Vertex Array Object containing draw details for filling polygons.
        gFillBuff (GLuint): Reference to Vertex Buffer Object storing geometry used to fill in polygon domainColors.
        ptBuff (GLuint): Reference to Vertex Buffer Object storing raw point geometry to be drawn by OpenGL hardware.
        ptCount (int): Total number of points to be rendered.

    Args:
        widget (object,optional): The parent object that will manage the OpenGL context for the hosting UI framework.
        refreshkey (str,optional): Name of function to call from `widget` whenever the draw state changes.
        getextKey (str,optional): Name of function to call from `widget` whenever draw extents are needed.

    Keyword Args:
        allowPolyPicking (bool,optional): If `True`, polygons are mouse-pickable; otherwise, clicking has no effect on polygons.
        allowPtPicking (bool,optional): If `True`, points are mouse-pickable; otherwise, clicking has no effect on polygons.
        useThicklines (bool,optional): If true, use thick lines for selection.
        beginContextKey (str,optional): Identifier of method to invoke on parent widget to enter an OpenGL drawing state.
        endContextKey (str,optional): Identifier of method to invoke on parent widget to exit an OpenGL drawing state.
        drawRubberBand (bool,optional): If `True` draw the rubberband box using the previous set coordinates.
        polygonColor (glm.vec4,optional): The default polygon color in 4-channel RGBA [0,1].
        pointColor (glm.vec4,optional): The default point color in 4-channel RGBA [0,1].
        gridColor (glm.vec4,optional): The color to apply to polygon outlines in 4-channel RGBA [0,1].
        pointSelectColor (glm.vec4,optional): The selected point color in 4-channel RGBA [0,1].
        selectLineColor1 (glm.vec4,optional): First color to apply to line selection overlay 4-channel RGBA [0,1].
        selectLineColor2 (glm.vec4,optional): Second color to apply to line selection overlay 4-channel RGBA [0,1].
        selectPolyColor1 (glm.vec4,optional): First color to apply to polygon fill selection overlay 4-channel RGBA [0,1].
        selectPolyColor2 (glm.vec4,optional): Second color to apply to polygon fill selection overlay 4-channel RGBA [0,1].
        fillSelections (bool,optional): If `True` apply selection overlay to the interior of selected polygons
        outlineSelections (bool,optional): If `True`, the selection overlay is applied to the perimeter of a selected polygon.
        fillPolygons (bool,optional): If `True`, fills the interior of polygons with the appropriate color.
        fillWithGradient (bool,optional): If `True`, fill with contents of reference gradient values, if present.
    """

    @staticmethod
    def getNextId():

        def _idGen():
            id = 0
            while True:
                yield id
                id += 1

        if not hasattr(GeometryGLScene.getNextId, 'gen'):
            GeometryGLScene.getNextId.gen = _idGen()
        return next(GeometryGLScene.getNextId.gen)

    # <editor-fold desc="Initializer Functions">
    def __init__(self, widget=None, refreshkey='', getextKey='', **kwargs):

        self.widget = widget
        self.refreshkey = refreshkey
        self.extentkey = getextKey

        # user setable formatting options
        self.beginContextKey = kwargs.get('beginContextKey', '')
        self.endContextKey = kwargs.get('endContextKey', '')
        self.drawRubberBand = kwargs.get('drawRubberBand', False)
        self._useThicklines = kwargs.get('useThicklines', False)
        self._useSelThicklines = kwargs.get('useSelectThicklines', True)
        self._ptColor = kwargs.get('defaultPointColor', glm.vec4(1, 0, 0, 1))
        self._ptSelectColor = kwargs.get('pointSelectColor', glm.vec4(0., 1., 1., 1.))
        self._gridColor = kwargs.get('defaultGridColor', glm.vec4(0, 0, 0, 1))
        self._fillColor = kwargs.get('defaultPolygonColor', glm.vec4(0.8, 0.8, 0.8, 1))
        self._selectLineColor1 = kwargs.get('selectLineColor1', glm.vec4(1., 1.0, 0., 1.0))
        self._selectLineColor2 = kwargs.get('selectLineColor2', glm.vec4(0., .0, 0., 1.0))
        self._selectPolyColor1 = kwargs.get('selectPolyColor1', glm.vec4(1., 1.0, 0., 0.25))
        self._selectPolyColor2 = kwargs.get('selectPolyColor2', glm.vec4(0., .0, 0., 0.25))
        self._rbColor1 = kwargs.get('rubberbandColor1',glm.vec4(0.,0.,0.,1.))
        self._rbColor2 = kwargs.get('rubberbandColor2', glm.vec4(1., 1., 1., 1.))
        self._fillSelect = kwargs.get('fillSelections', True)
        self._lineSelect = kwargs.get('outlineSelections', True)
        self._fillGrid = kwargs.get('fillPolygons', True)
        self._gradientGrid = kwargs.get('fillWithGradient', False)
        self._allowPolyPicking = kwargs.get('allowPolyPicking', False)
        self._allowPtPicking = kwargs.get('allowPtPicking', False)
        self._allowLinePicking = kwargs.get('allowLinePicking', False)
        self._doDrawAxes = kwargs.get('drawAxes', False)
        self._axTickCount = kwargs.get('axesTickCount', 0)

        if 'selectLineSingleColor' in kwargs:
            self._selectLineColor1 = kwargs['selectLineSingleColor']
            self._selectLineColor2 = kwargs['selectLineSingleColor']

        if 'selectPolySingleColor' in kwargs:
            self._selectPolyColor1 = kwargs['selectPolySingleColor']
            self._selectPolyColor2 = kwargs['selectPolySingleColor']

        self._txtFontPath = kwargs.get('labelFont',
                          os.path.join(os.path.dirname(__file__), 'ubuntu-font-family-0.83', 'Ubuntu-M.ttf'))
        self._txtPtSize = kwargs.get('labelPt', 18)
        self._txtRdr = None

        self._initialized = False
        self._widthDominant = False
        self._aspectRatio = 1
        self._offs_ratio = 0
        self._vheight = 0
        self._vwidth = 0
        self._frameBuff = 0
        self._fbTex = 0
        self._fbRbo = 0
        self.SetExtents(-1, 1, -1, 1)
        self._identMat = glm.mat4(1.)
        self._viewMat = glm.mat4(1.)
        self._mdlMat = glm.mat4(1.)
        self._mvpMat = glm.mat4(1.)
        self._txtTransMat = glm.mat4(1.)
        self.rb_p2 = None
        self.rb_p1 = None
        self._zoomLevel=0
        self._mvpInvMat = glm.inverse(self._mvpMat)

        self._drawStack = []
        self._layers = {}
        self._pointLayerIds = set()
        self._polyLayerIds = set()
        self._lineLayerIds = set()
        self._rasterLayerIds = set()
        self._weakRefIds = set()

        self._gFillVao = 0
        self._gFillBuff = 0

        self._rbVao = 0
        self._rbBuff = 0

        self._axesVao = 0
        self._axesBuff = 0

        self._atlasVao = 0
        self._stringBuff = 0
        self._atlasTex = 0
        self._strVertCount = 0

        self._caches = {}

        self._eLeft = None
        self._eRight = None
        self._eTop = None
        self._eBottom = None

        self._selLineWidth = 5

        self._fullRefresh = True

    def initializeGL(self):
        """ Initializes the OpenGL subsystem. This will need to be called before any rendering can take place.

        """

        # for shader functions that use pds set to finest
        glHint(GL_FRAGMENT_SHADER_DERIVATIVE_HINT,GL_NICEST)
        # Set the clear color to white.
        glClearColor(1, 1, 1, 1)
        # glPointSize(2.0)
        glEnable(GL_PROGRAM_POINT_SIZE)

        glDisable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Disable the depth test since we don't need it for the time being.
        glDisable(GL_DEPTH_TEST)

        # load default shader and shader mappings
        self._progMgr = ShaderProgMgr()

        # build fill geometry to use for poly rendering
        self._gFillVao, self._rbVao = glGenVertexArrays(2)
        self._gFillBuff, self._rbBuff = glGenBuffers(2)
        fillVerts = np.array([-1., 1., -1., -1., 1., 1., 1., -1.], dtype=np.float32)
        self._LoadGLBuffer(fillVerts, None, LayerRecord(-1, self._gFillVao, self._gFillBuff, 4))

        # initialize rubberband data
        glBindVertexArray(self._rbVao)
        glBindBuffer(GL_ARRAY_BUFFER, self._rbBuff)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        glBufferData(GL_ARRAY_BUFFER, 32, None, GL_DYNAMIC_DRAW)
        glBindVertexArray(0)

        # grab any desired default values from any desired program
        # tmp = np.zeros([1], dtype=np.float32)
        # self._progMgr.useProgram('thickline')
        # glGetUniformfv(self._progMgr.shaderProgram, self._progMgr['width'], tmp)
        # self._selLineWidth = tmp[0]

        # Set initialized here so caches will be applied
        self._initialized = True

        # data can be assigned before the OpenGL subsystem is initialized and capable of accepting it.
        # if this is the case, load any cached data into the appropriate places in GPU memory.

        # apply any cached data
        for cache in self._caches.values():
            if 'fn' in cache:
                fn = getattr(self, cache['fn'])
                for args in cache['data']:
                    fn(*args)
            elif 'attr' in cache:
                setattr(self, cache['attr'], cache['data'])

        # once applied, clear caches
        self._caches.clear()

        # report any errors.
        # err = glGetError()
        # if err != 0:
        #     raise GaiaGLException(format(err))

        # set up texture locations for refColorTexProg
        with self.grabContext():
            # sampler indices shouldn't change, so just set them here
            self._progMgr.useProgram('text')
            glUniform1i(self._progMgr['textAtlas'], 3)
            self._progMgr.useProgram()

            self._updateMVP()

    # </editor-fold>

    # <editor-fold desc="Context / Widget Support Methods">
    def _beginContext(self):
        if len(self.beginContextKey) > 0:
            getattr(self.widget, self.beginContextKey)()

    def _endContext(self):
        if len(self.endContextKey) > 0:
            getattr(self.widget, self.endContextKey)()

    def _doRefresh(self):
        """Call the widget's refresh function."""
        getattr(self.widget, self.refreshkey, dummyFn)()

    @contextmanager
    def grabContext(self):
        self._beginContext()
        try:
            # return nothing; context is host-code specific
            yield
        finally:
            self._endContext()

    def GetGLExtents(self):
        """Get the extents of the OpenGL canvas."""
        return getattr(self.widget, self.extentkey, dummyFn)()

    # </editor-fold>

    # <editor-fold desc="Draw Functions">
    @staticmethod
    def _drawThickLineGL(start, count):
        glDrawArrays(GL_LINE_STRIP_ADJACENCY, start,count)

    def paintGL(self):
        """Method responsible for applying draw instructions to the OpenGL state machine."""

        if self._initialized:

            # set the viewport here to ensure that the values are maintained.
            glViewport(*self._dims)

            if self._fullRefresh:
                existBuffer = np.empty([1], np.int32)
                glGetIntegerv(GL_FRAMEBUFFER_BINDING, existBuffer)
                glBindFramebuffer(GL_FRAMEBUFFER, self._frameBuff)


                # cache directly referenced shader programs
                simpleProg = self._progMgr.progLookup('simple')
                refColorTexProg = self._progMgr.progLookup('refColorTex')

                # clear the color, depth, and stencil buffers.
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
                glViewport(*self._dims)
                # populate programs with matrix
                for progName in ('thickline','refline'):
                    self._progMgr.useProgram(progName)
                    glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))
                # # load and assign base shader program.
                # if self._gradientGrid and not self.refTex:
                #     self._gradientGrid = False
                #     # fall back to solid fill
                #     self._fillGrid = True

                # load and assign base shader program.
                self._progMgr.useProgramDirectly(refColorTexProg)
                glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))
                self._progMgr.useProgramDirectly(simpleProg)
                glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))

                lastProg = self._progMgr.shaderProgram
                layerId = 0

                for rec in reversed(self._drawStack):

                    theType = type(rec)
                    if theType == ReferenceRecord:
                        theType = type(rec.srcRecord)
                    self._UpdateSelections(rec.id)
                    if theType == PolyLayerRecord:
                        baseProg = simpleProg if rec.fillMode != POLY_FILL.TEX_REF else refColorTexProg
                        if baseProg != lastProg:
                            self._progMgr.useProgramDirectly(baseProg)
                            lastProg = baseProg
                        self._drawPolyLayer(rec)
                    elif theType == PointLayerRecord:
                        self._drawPointLayer(rec)
                    elif theType == LineLayerRecord:
                        self._drawLineLayer(rec)
                    elif theType in (RasterLayerRecord,RasterIndexLayerRecord):
                        self._drawRaster(rec)

                    layerId += 1

                glBindFramebuffer(GL_FRAMEBUFFER, existBuffer[0])

                # draw Axes if available
                self._drawAxes()
                self._fullRefresh = False

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
            glBindVertexArray(self._gFillVao)
            self._progMgr.useProgram('fbBlit')
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self._fbTex)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

            if self.drawRubberBand and self.rb_p1 is not None and self.rb_p2 is not None:
                self._progMgr.useProgram('rubberBand')
                glBindVertexArray(self._rbVao)
                glDrawArrays(GL_LINE_LOOP, 0, 4)

            # Clear active shader program.
            self._progMgr.useProgram()

            # Print any errors encountered by the OpenGL state machine.
            err = glGetError()
            if err != 0:
                raise GaiaGLException(format(err))

            glFinish()

    def _drawPolyLayer(self, rec, pickMode=False):

        # TODO: Reconfigure to use glMultiDrawArrays.

        #  Fill polygons
        # Since the polys are all 2D, we can use a neat trick with the
        # stencil buffer to properly fill the polygons without requiring tessallation.

        if rec.draw and len(rec.groups) > 0:
            if not pickMode:
                glEnable(GL_BLEND)
            # fill
            # if self._polyColors is None:

            for c, poly in enumerate(rec.groups):

                if rec.fillGrid and (
                        self._fillGrid or self._fillSelect or rec.fillMode == POLY_FILL.TEX_REF) or pickMode:

                    # load and assign base shader program.
                    self._progMgr.useProgram('simple')
                    glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))

                    # activate the stencil buffer and tell it to toggle between 1 and 0 every time a pixel is hit.
                    glEnable(GL_STENCIL_TEST)
                    glStencilOp(GL_INVERT, GL_INVERT, GL_INVERT)

                    if pickMode or rec.fillMode != POLY_FILL.TEX_REF or rec.refTex == 0:
                        self._assignPolyFillColor(pickMode, rec, c)

                    glBindVertexArray(rec.vao)

                    # prep the stencil buffer for writing, and disable the color buffer.
                    glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
                    glStencilFunc(GL_ALWAYS, 1, 1)

                    # Render to the stencil buffer, creating a "stencil" for use with filling the polygon.
                    for ring in poly:
                        glDrawArrays(GL_TRIANGLE_FAN, ring[0],ring[1]-2)

                    # Enable the color buffer, change the stencil buffer to read only, and load the geometry to use in fill
                    # operations.
                    glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
                    glStencilFunc(GL_EQUAL, 1, 1)
                    glStencilOp(GL_ZERO, GL_KEEP, GL_KEEP)

                    if rec.fillMode != POLY_FILL.TEX_REF or rec.refTex == 0:
                        mLoc = self._progMgr['mvpMat']

                        if rec.attrVals is not None and rec.fillMode == POLY_FILL.VAL_REF:  # and rec.useFillAttrVals:
                            self._progMgr.useProgram('refColorVal')
                            glUniform1f(self._progMgr['refValue'], rec.attrVals[c])
                            mLoc = self._progMgr['mvpMat']
                            if rec.customGradTexes[POLY_GRAD_IND.VAL] != 0:
                                glUniform1i(self._progMgr['customGradient'], 1)
                            else:
                                glUniform1i(self._progMgr['customGradient'], 0)
                        glBindVertexArray(self._gFillVao)
                        glUniformMatrix4fv(mLoc, 1, GL_FALSE, glm.value_ptr(self._identMat))

                    else:
                        glBindVertexArray(rec.refVao)
                        self._progMgr.useProgram('refColorTex')
                        glBindTextures(0, 2, [rec.refTex, rec.customGradTexes[POLY_GRAD_IND.REF]])
                        glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))

                        if rec.customGradTexes[POLY_GRAD_IND.REF] != 0:
                            glUniform1i(self._progMgr['customGradient'], 1)
                        else:
                            glUniform1i(self._progMgr['customGradient'], 0)

                    # use a piece of geometry that covers the entire screen, and fill with the polygon's assigned color.
                    # The previously created stencil will only allow the color to be applied within the boundaries of the
                    # polygon.
                    if pickMode or self._fillGrid or rec.fillMode == POLY_FILL.TEX_REF:
                        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

                    if not pickMode and self._fillSelect and rec.selectedRecs[c] == 1:
                        glEnable(GL_BLEND)
                        self._progMgr.useProgram('selectPoly')
                        glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._identMat))
                        glUniform4fv(self._progMgr['inColor1'], 1, glm.value_ptr(self._selectPolyColor1))
                        glUniform4fv(self._progMgr['inColor2'], 1, glm.value_ptr(self._selectPolyColor2))
                        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

                    self._progMgr.useProgram('simple')

                    # Reset transformations and clear the stencil buffer for the next polygon to be rendered.

                    glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))
                    glClear(GL_STENCIL_BUFFER_BIT)
                    glDisable(GL_STENCIL_TEST)

                # DO Polygon outlines
                # Uses line loops to draw polygon rings; very straightforward.
                # Note that glLineWidth is deprecated, and does not work for a number
                # of implementations. Best way to handle would be to use a geometry shader to convert
                # lines from to triangle strips.
                if not pickMode and rec.drawGrid:

                    glBindVertexArray(rec.vao)

                    # if rec.selectedRecs[c]==0:
                    if rec.line_thickness == 1:
                        self._progMgr.useProgram('simple')
                        glUniform4fv(self._progMgr['inColor'], 1, glm.value_ptr(rec.gridColor))
                        for ring in poly:
                            # keep as line strip to avoid issues with gradObj lines
                            glDrawArrays(GL_LINE_STRIP_ADJACENCY, *ring)
                    else:
                        self._progMgr.useProgram('thickline')
                        glUniform1f(self._progMgr['width'], rec.line_thickness)
                        glUniform4fv(self._progMgr['inColor1'], 1, glm.value_ptr(rec.gridColor))
                        glUniform4fv(self._progMgr['inColor2'], 1, glm.value_ptr(rec.gridColor))


                        for start,count in poly:
                            GeometryGLScene._drawThickLineGL(start,count)


            # Draw selected poly outlines here, on top of everything else
            if not pickMode and rec.drawGrid and self._lineSelect:
                glBindVertexArray(rec.vao)
                if self._useSelThicklines:

                    self._progMgr.useProgram('thickline')
                    glUniform1f(self._progMgr['width'], self._selLineWidth)
                    glUniform4fv(self._progMgr['inColor1'], 1, glm.value_ptr(self._selectLineColor1))
                    glUniform4fv(self._progMgr['inColor2'], 1, glm.value_ptr(self._selectLineColor2))


                    c = 0
                    for poly in rec.groups:
                        if rec.selectedRecs[c] == 1:
                            for start,count in poly:
                                # glDrawArrays(GL_LINE_LOOP, *ring)
                                GeometryGLScene._drawThickLineGL(start,count)
                        c += 1
                else:
                    self._progMgr.useProgram('simple')
                    glUniform4fv(self._progMgr['inColor'], 1, glm.value_ptr(self._selectLineColor1))
                    c = 0
                    for poly in rec.groups:
                        if rec.selectedRecs[c] == 1:
                            for ring in poly:
                                # glDrawArrays(GL_LINE_LOOP, *ring)
                                glDrawArrays(GL_LINE_STRIP_ADJACENCY, *ring)
                        c += 1

                self._progMgr.useProgram('simple')

            glDisable(GL_BLEND)
            # Clear the active VBO and VAO
            glBindVertexArray(0)

    def _drawPointLayer(self, rec, pickMode=False):

        #  Draw points.

        if rec.colorMode==POINT_FILL.SINGLE:
            glVertexAttrib4f(2,*rec.geomColors[0].color)
        
        if rec.ptSize is not None:
            glVertexAttrib1f(3,rec.ptSize)
        if rec.glyphCode is not None:
            glVertexAttribI1ui(4,ord(rec.glyphCode))
        if rec.draw and rec.count > 0 and rec.buff != 0:
            glBindVertexArray(rec.vao)
            # glPointSize(rec.ptSize)

            if rec.colorMode in [POINT_FILL.SINGLE,POINT_FILL.GROUP,POINT_FILL.INDEX]:
                self._progMgr.useProgram('point')
                glUniformMatrix4fv(self._progMgr['pMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))
                # glUniform1f(self._progMgr['ptScale'], rec.ptSize)

                if not pickMode:
                    glEnable(GL_BLEND)
                    glUniform4fv(self._progMgr['selectColor'], 1, glm.value_ptr(self._ptSelectColor))
                    if rec.colorMode == POINT_FILL.GROUP:
                        for gc in rec.geomColors:
                            glUniform4fv(self._progMgr['inColor'], 1, glm.value_ptr(gc.color))
                            # Render the points
                            glDrawArrays(GL_POINTS, gc.start, gc.count)
                    else: # POINT_FILL.SINGLE
                        glDrawArrays(GL_POINTS,0,rec.count)
                else:
                    # note: current implementation is extremely innefficient
                    for i in range(rec.count):
                        color = self._getRecordIdColor(rec.id,i)

                        glUniform4fv(self._progMgr['selectColor'], 1, glm.value_ptr(color))
                        glUniform4fv(self._progMgr['inColor'], 1, glm.value_ptr(color))
                        glDrawArrays(GL_POINTS, i, 1)

            else:  # POINT_FILL.VAL_REF
                glEnable(GL_BLEND)
                glActiveTexture(GL_TEXTURE1)
                glBindTexture(GL_TEXTURE_1D, rec.gradTexId)
                self._progMgr.useProgram('refPoint')
                glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))
                glUniform2f(self._progMgr['valueBoundaries'], rec.lowVal, rec.highVal)
                glUniform1i(self._progMgr['clampGradient'], 1 if rec.clampColorToRange else 0)
                glUniform1i(self._progMgr['customGradient'], 1)

                # glEnable(GL_PROGRAM_POINT_SIZE)
                if not rec.scaleByValue:
                    glUniform2f(self._progMgr['refSizeRange'], rec.ptSize, rec.ptSize)
                else:
                    glUniform2f(self._progMgr['refSizeRange'],rec.scaleMinSize,rec.scaleMaxSize)
                glDrawArrays(GL_POINTS, 0, rec.count)
                # glDisable(GL_PROGRAM_POINT_SIZE)

            glDisable(GL_BLEND)
            # Clear active VBO and VAO.
            glBindVertexArray(0)

    def _drawLineLayer(self,rec,pickMode=False):

        if rec.draw and rec.count > 0 and rec.buff != 0:
            glBindVertexArray(rec.vao)

            if not pickMode:
                if rec.colorMode == LINE_FILL.SINGLE:
                    glEnable(GL_BLEND)
                    if rec.line_thickness == 1:
                        self._progMgr.useProgram('simple')
                        glUniform4fv(self._progMgr['inColor'], 1, glm.value_ptr(rec.geomColors[0]))
                        for offs, count in rec.groups:
                            glDrawArrays(GL_LINE_STRIP_ADJACENCY, offs, count)
                    else:
                        self._progMgr.useProgram('thickline')
                        glUniform1f(self._progMgr['width'],rec.line_thickness)
                        glUniform4fv(self._progMgr['inColor1'], 1, glm.value_ptr(rec.geomColors[0]))
                        glUniform4fv(self._progMgr['inColor2'], 1, glm.value_ptr(rec.geomColors[0]))

                        for offs, count in rec.groups:
                            GeometryGLScene._drawThickLineGL(offs,count)

                else: # LINE_FILL.VAL_REF:
                    self._progMgr.useProgram('refline')
                    glActiveTexture(GL_TEXTURE1)
                    glBindTexture(GL_TEXTURE_1D, rec.gradTexId)
                    glUniform1f(self._progMgr['width'], rec.line_thickness)
                    glUniform2f(self._progMgr['valueBoundaries'], rec.lowVal, rec.highVal)
                    glUniform1i(self._progMgr['customGradient'], 1)

                    for offs, count in rec.groups:
                        GeometryGLScene._drawThickLineGL(offs, count)

                # draw any selected as an overlay, just in case select thickness is less than line thickness
                if any(rec.selectedRecs):
                    self._progMgr.useProgram('thickline')
                    glUniform1f(self._progMgr['width'], self._selLineWidth)
                    glUniform4fv(self._progMgr['inColor1'], 1, glm.value_ptr(self._selectLineColor1))
                    glUniform4fv(self._progMgr['inColor2'], 1, glm.value_ptr(self._selectLineColor2))

                    for i, (offs, count) in enumerate(rec.groups):
                        if rec.selectedRecs[i]:
                            GeometryGLScene._drawThickLineGL(offs, count)

            else:
                # if line isn't thick, widen a bit to make it easier to pick
                useThickness = rec.line_thickness if rec.line_thickness > 1 else 2
                self._progMgr.useProgram('thickline')
                glUniform1f(self._progMgr['width'], useThickness)

                for i, (offs, count) in enumerate(rec.groups):
                    color = self._getRecordIdColor(rec.id, i)
                    glUniform4fv(self._progMgr['inColor1'], 1, glm.value_ptr(color))
                    glUniform4fv(self._progMgr['inColor2'], 1, glm.value_ptr(color))

                    GeometryGLScene._drawThickLineGL(offs, count)

            glDisable(GL_BLEND)
            # Clear active VBO and VAO.
            glBindVertexArray(0)

    def _drawRaster(self, rec, pickMode=False):

        if rec.draw and rec.count > 0 and rec.buff != 0:
            glBindVertexArray(rec.vao)

            if not isinstance(rec, RasterIndexLayerRecord) or pickMode:
                self._progMgr.useProgram('raster')
                glUniform1i(self._progMgr['isSelect'], 1 if pickMode else 0)
                glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))
            else:
                glActiveTexture(GL_TEXTURE1)
                glBindTexture(GL_TEXTURE_1D, rec.gradTexId)
                self._progMgr.useProgram('refColorTex')
                glUniformMatrix4fv(self._progMgr['mvpMat'],1,GL_FALSE,glm.value_ptr(self._mvpMat))
                glUniform2f(self._progMgr['valueBoundaries'], rec.lowVal, rec.highVal)
                glUniform1i(self._progMgr['clampGradient'],1 if rec.clampColorToRange else 0)
                glUniform1i(self._progMgr['customGradient'],1)

            if not pickMode:
                glEnable(GL_BLEND)
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, rec.texId)
                glDrawArrays(GL_TRIANGLE_FAN, 0, rec.count)
            else:
                color = self._getRecordIdColor(rec.id)

                glUniform4fv(self._progMgr['selectColor'], 1, glm.value_ptr(color))
                glDrawArrays(GL_TRIANGLE_FAN, 0, rec.count)

            glDisable(GL_BLEND)
            # Clear active VBO and VAO.
            glBindVertexArray(0)

    def _drawAxes(self):

        if self._doDrawAxes and self._axesVao != 0:
            glBindVertexArray(self._axesVao)
            self._progMgr.useProgram('axes')
            glUniformMatrix4fv(self._progMgr['txtProjMat'], 1, GL_FALSE, glm.value_ptr(self._textProjMat))
            glUniformMatrix4fv(self._progMgr['txtViewMat'], 1, GL_FALSE, glm.value_ptr(self._viewMat * self._textProjMat))
            # glUniform4fv(self.sp_colorLoc, 1, glm.value_ptr(glm.vec4(0.,0.,0.,1.)))
            glDrawArrays(GL_LINES, 0, 4)

            self._progMgr.useProgram('text')
            glEnable(GL_BLEND)
            glBindVertexArray(self._atlasVao)
            glActiveTexture(GL_TEXTURE3)
            glBindTexture(GL_TEXTURE_2D, self._atlasTex)
            glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._textProjMat))
            glUniformMatrix4fv(self._progMgr['txtViewMat'], 1, GL_FALSE, glm.value_ptr(self._viewMat))

            glDrawArrays(GL_TRIANGLES, 0, self._strVertCount)

            glDisable(GL_BLEND)


    def _regenFramebuffer(self, width, height):

        glDeleteFramebuffers(1, [self._frameBuff])
        glDeleteTextures(1, [self._fbTex])
        glDeleteRenderbuffers(1, [self._fbRbo])

        self._frameBuff = glGenFramebuffers(1)
        self._fbTex = glGenTextures(1)

        # activate framebuffer
        existBuffer = np.empty([1], np.int32)
        glGetIntegerv(GL_FRAMEBUFFER_BINDING, existBuffer)
        glBindFramebuffer(GL_FRAMEBUFFER, self._frameBuff)

        # build target texture
        glBindTexture(GL_TEXTURE_2D, self._fbTex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

        # add renderbuffer for stencil support
        self._fbRbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self._fbRbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self._fbRbo)

        # wire up framebuffer

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._fbTex, 0)
        glDrawBuffers(1, np.array([GL_COLOR_ATTACHMENT0]))

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise GaiaGLException("Framebuffer failed to initialize.")

        glViewport(0, 0, width, height)
        glBindFramebuffer(GL_FRAMEBUFFER, existBuffer[0])

        self.markFullRefresh()

    def markFullRefresh(self):
        self._fullRefresh = True

    # </editor-fold>

    # <editor-fold desc="Extent Methods">
    def resizeGL(self, width, height):
        """Resize operations for the OpenGL context.

        Args:
            width (int): The new width of the viewport.
            height (int): The new height of the viewport.

        """

        # Attempt to maintain the source aspect ratio through viewport offsetting.
        cwidth = int(height / self._aspectRatio)
        cheight = int(self._aspectRatio * width)

        self._dims = None
        # if width < cwidth:
        #     self._dims = 0, (height - cheight) // 2, width, cheight
        # else:
        #     self._dims = (width - cwidth) // 2, 0, cwidth, height

        self._dims = 0, 0, width, height
        self._widthDominant = width < cwidth
        if self._widthDominant:
            offs_ratio = height / cheight
        else:
            offs_ratio = width / cwidth

        if self._offs_ratio != offs_ratio:
            # oldExts=self.getScreenExts()
            self._offs_ratio = offs_ratio
            self.updateProjMat()
            self._updateMVP()
            # self.zoomToExts(*oldExts)

            # adjust line thickness to reflect ratio
            for progName in ('thickline','refline'):
                thickProg = self._progMgr.progLookup(progName)
                if thickProg != 0:
                    self._progMgr.useProgramDirectly(thickProg)
                    glUniform2f(self._progMgr['resolution'], width, height)


            # set textProjection
            # self._textProjMat = glm.ortho(0, width, 0, height, 1.0, -1.0)
            # self.refreshTextTransMat()
            #

            if self._initialized:
                self._regenFramebuffer(width, height)

    def SetExtents(self, left, right, bottom, top, margin=0.05):
        """ Set the extents for the orthogonal view

        Args:
            left (float): The left extent.
            right (float): The right extent.
            bottom (float): The bottom extent.
            top (float): The top extent.
            margin (float,optional): The margin to pad each extent with as a fraction of width or height as appropriate.

        """

        extsChanged = not hasattr(self, '_eLeft') or \
                      self._eLeft != left or \
                      self._eRight != right or \
                      self._eBottom != bottom or \
                      self._eTop != top

        if extsChanged:
            # cache extents for future use
            self._eLeft = left
            self._eRight = right
            self._eBottom = bottom
            self._eTop = top
            self._eMargin = margin

            width = float(self._eRight - self._eLeft)
            height = float(self._eTop - self._eBottom)
            self._aspectRatio = height / width if width != 0 else 0  # height/width

            self.updateProjMat()

            # refresh the view
            if self._initialized:
                size = self.GetGLExtents()
                self.resizeGL(size.width, size.height)
                self._progMgr.useProgram('point')
                # glUniform1f(self._pt_aspectLoc, self._aspectRatio)
                self._updateMVP()
                self._doRefresh()

                # TODO: fix data leak into polygon layer before re-enabling
                # self._CreateAxes(self._eLeft, self._eRight, self._eBottom, self._eTop, 5)
            self.markFullRefresh()

    def SetMaxExtents(self, left, right, bottom, top):
        """ Assign extents only if greater than the currently assigned extent.

        Args:
            left (float): The left extent.
            right (float): The right extent.
            bottom (float): The bottom extent.
            top (float): The top extent.

        """

        if self._eLeft is not None:
            self.SetExtents(min(self._eLeft, left),
                            max(self._eRight, right),
                            min(self._eBottom, bottom),
                            max(self._eTop, top)
                            )
        else:
            self.SetExtents(left, right, bottom, top)

    def recalcMaxExtentsFromLayers(self):
        self._eLeft = None
        self._eRight = None
        self._eBottom = None
        self._eTop = None

        for lyr in self._layers.values():
            if lyr.exts is not None:
                self.SetMaxExtents(*lyr.exts)

    # </editor-fold>

    # <editor-fold desc="Decoration Properties">
    @property
    def fillPolygons(self):
        """bool: flag indicating whether or not the polygons are being filled with the assigned color."""
        return self._fillGrid

    @property
    def defaultPointColor(self):
        """numpy.array: normalized color channel values to be applied to all points in (R,G,B) ordering."""
        return self._ptColor

    @property
    def defaultGridColor(self):
        """numpy.array: normalized color channel values to be applied to all polygon outlines in (R,G,B) ordering."""
        return self._gridColor

    @property
    def defaultPolygonColor(self):
        """numpy.array: normalized color channel values to be applied to all polygon interiors in (R,G,B) ordering."""
        return self._fillColor

    @property
    def selectColor(self):
        return self._selectLineColor1

    @property
    def pointSelectColor(self):
        return self._selectLineColor1

    @property
    def allowPicking(self):
        return any([self._allowPolyPicking,self._allowPtPicking,self._allowLinePicking])

    @property
    def allowPolyPicking(self):
        return self._allowPolyPicking

    @property
    def allowPtPicking(self):
        return self._allowPtPicking

    @property
    def allowLinePicking(self):
        return self._allowLinePicking

    @property
    def backgroundColor(self):
        """numpy.array: normalized color channel values to be applied to the background in (R,G,B) ordering. This
        is a write-only attribute."""
        raise ValueError('"backgroundColor" attribute is write-only')

    @property
    def polygonSelectionFill(self):
        return self._fillSelect

    @property
    def polygonSelectionOutline(self):
        return self._lineSelect

    @property
    def selectFillColors(self):
        return (self._selectPolyColor1, self._selectPolyColor2)

    @property
    def selectLineColors(self):
        return (self._selectLineColor1, self._selectLineColor2)

    @property
    def doDrawAxes(self):
        return self._doDrawAxes

    @property
    def axesTickCount(self):
        return self._axTickCount

    @property
    def layerCount(self):
        return len(self._layers)

    @property
    def initialized(self):
        return self._initialized

    @property
    def rubberBandColors(self):
        return (self._rbColor1,self._rbColor2)

    @fillPolygons.setter
    def fillPolygons(self, doFill):
        self._fillGrid = doFill
        self.markFullRefresh()
        self._doRefresh()

    @defaultPointColor.setter
    def defaultPointColor(self, c):
        self._ptColor = c

    @defaultGridColor.setter
    def defaultGridColor(self, c):
        self._gridColor = c

    @defaultPolygonColor.setter
    def defaultPolygonColor(self, c):
        self._fillColor = c

    @selectColor.setter
    def selectColor(self, c):
        self._selectLineColor1 = c
        self.markFullRefresh()
        self._doRefresh()

    @pointSelectColor.setter
    def pointSelectColor(self, c):
        self._ptSelectColor = c
        self.markFullRefresh()
        self._doRefresh()

    @backgroundColor.setter
    def backgroundColor(self, c):
        if self._initialized:
            with self.grabContext():
                glClearColor(c.r, c.g, c.b, c.a)
            self.markFullRefresh()
            self._doRefresh()
        else:
            self._caches['bgColor'] = {'attr': 'backgroundColor', 'data': c}

    @polygonSelectionFill.setter
    def polygonSelectionFill(self, fill):
        self._fillSelect = fill
        self.markFullRefresh()
        self._doRefresh()

    @polygonSelectionOutline.setter
    def polygonSelectionOutline(self, line):
        self._lineSelect = line
        self.markFullRefresh()
        self._doRefresh()

    @selectFillColors.setter
    def selectFillColors(self, colors):
        if isinstance(colors, glm.vec4):
            self._selectPolyColor1, self._selectPolyColor2 = colors, colors
        else:
            self._selectPolyColor1, self._selectPolyColor2 = glm.vec4(colors[0]), glm.vec4(colors[1])
        self.markFullRefresh()
        self._doRefresh()

    @selectLineColors.setter
    def selectLineColors(self, colors):
        if isinstance(colors, glm.vec4):
            self._selectLineColor1, self._selectLineColor2 = colors, colors
        else:
            self._selectLineColor1, self._selectLineColor2 = glm.vec4(colors[0]), glm.vec4(colors[1])
        self.markFullRefresh()
        self._doRefresh()

    @doDrawAxes.setter
    def doDrawAxes(self, doDraw):
        self._doDrawAxes = doDraw
        self.markFullRefresh()
        self._doRefresh()

    @axesTickCount.setter
    def axesTickCount(self, count):
        self._axTickCount = count
        if self._initialized:
            self._progMgr.useProgram('axes')
            glUniform1i(self._progMgr['subTickCount'], self._axTickCount)
            self.markFullRefresh()
            self._doRefresh()

    @rubberBandColors.setter
    def rubberBandColors(self, value):

        if isinstance(value, glm.vec4):
            rbc1 = rbc2 = value
        else:
            rbc1, rbc2 = value
        if self._rbColor1 != rbc1 or self._rbColor2 != rbc2:
            self._rbColor1 = rbc1
            self._rbColor2 = rbc2
            self._updateRubberBandColor()
            self._doRefresh()

    # </editor-fold>

    # <editor-fold desc="Add Layers">
    def _addVectorRecord(self, verts, ext, rec, extra=None):

        with self.grabContext():
            rec.vao = glGenVertexArrays(1)
            verts,extra = rec.prepareForGLLoad(verts,ext,extra)
            self._LoadGLBuffer(verts, ext, rec, extra)

    def _addRasterRecord(self, pxlData, channels, rec,internal=None, gradObj=None):

        with self.grabContext():
            rec.vao = glGenVertexArrays(1)
            verts,_ = rec.prepareForGLLoad(None,rec.exts,None)

            texCoords = np.array([0., 0.,
                                  0., 1.,
                                  1., 1.,
                                  1., 0., ], dtype=np.float32)
            self._LoadGLBuffer(verts, tuple(rec.exts), rec, texCoords)
            # glBindVertexArray(rec.vao)
            self._LoadTexture(pxlData, GL_TEXTURE0, GL_TEXTURE_2D, channels, rec.texId,internal,interp=rec.smooth)
            # glBindVertexArray(0)

            if isinstance(rec, RasterIndexLayerRecord) and gradObj is not None:
                gradTex = gradObj.colorStrip(64,True)
                self._LoadTexture(gradTex, GL_TEXTURE1, GL_TEXTURE_1D,GL_RGBA,rec.gradTexId,interp=True)


    def _registerLayer(self, rec):
        self._drawStack.append(rec)
        self._layers[rec.id] = rec
        self.markFullRefresh()

    def AddPointLayer(self, verts, ext, **kwargs):
        """Set the points to be rendered.

        Args:
            verts (numpy.array): 1D array of vertex components to be rendered as points.
            ext (tuple): Minimum extents to apply; extents are in the order of (left, right, bottom, top).

        Returns:
            int: Index of new list.
        """

        id = GeometryGLScene.getNextId()
        if not any([kw in kwargs for kw in ('single_color','group_colors','indexed_colors','value_gradient')]):
            kwargs['single_color'] = self._ptColor
        rec = PointLayerRecord(id, count=len(verts) // 2, exts=ext,**kwargs)
        attribVals = kwargs.get('attrib_data',None)
        self._loadPointLayer(rec, ext, verts,attribVals)
        return id

    def AddPolyLayer(self, verts, polygroups, ext, **kwargs):
        """Set the polygons to be rendered.

        Args:
            verts (numpy.array): 1D array of vertex components to be rendered as points composing the polygon rings.
            polygroups (list): A list of lists of start indices and lengths. These are used to describe how to draw
              the contents of `verts` as polygons.
            ext (tuple): Minimum extents to apply; extents are in the order of (left, right, bottom, top).

        Returns:
            int: Index of new list.
        """

        id = GeometryGLScene.getNextId()
        extKeys = {'grid_color': self._gridColor,
                   'single_color': self._fillColor}
        extKeys.update(kwargs)

        rec = PolyLayerRecord(id, polygroups=polygroups, exts=ext, **extKeys)

        self._loadPolyLayer(rec, ext, verts)
        return id

    def AddLineLayer(self,verts,ext,linecount=None,linegroups=None,values=None,**kwargs):

        id = GeometryGLScene.getNextId()
        extKeys = {'single_color': self._fillColor}
        extKeys.update(kwargs)

        rec = LineLayerRecord(id, segmentcount=linecount,linegroups=linegroups, exts=ext, **extKeys)
        if values is not None:
            rec.colorMode = LINE_FILL.VAL_REF
        self._loadLineLayer(rec, ext, verts,values)
        return id


    def _loadPointLayer(self, rec, ext, verts,attribVals=None):
        self._registerLayer(rec)

        self._pointLayerIds.add(rec.id)

        if self._initialized:
            self._addVectorRecord(verts, ext, rec,attribVals)
        else:
            cache = self._caches.setdefault('ptData', {'fn': '_addVectorRecord', 'data': []})
            cache['data'].append((verts, ext, rec,attribVals))

    def _loadPolyLayer(self, rec, ext, verts):
        self._registerLayer(rec)

        self._polyLayerIds.add(rec.id)
        if self._initialized:
            self._addVectorRecord(verts, ext, rec)
        else:
            cache = self._caches.setdefault('polyData', {'fn': '_addVectorRecord', 'data': []})
            cache['data'].append((verts, ext, rec))

    def _loadLineLayer(self, rec, ext, verts,refVals=None):
        self._registerLayer(rec)

        self._lineLayerIds.add(rec.id)
        if self._initialized:
            self._addVectorRecord(verts, ext, rec,refVals)
        else:
            cache = self._caches.setdefault('lineData', {'fn': '_addVectorRecord', 'data': []})
            cache['data'].append((verts, ext, rec,refVals))

    def _loadReferenceLayer(self, rec):

        if rec.exts is not None:
            self.SetMaxExtents(*rec.exts)
        self._registerLayer(rec)
        idSet = self._typeSetForRec(rec)
        idSet.add(rec.id)

    def _loadRasterLayer(self, pxlData, channels, rec,internal=None,gradObj=None):
        self._registerLayer(rec)
        self._rasterLayerIds.add(rec.id)

        if self._initialized:
            self._addRasterRecord(pxlData, channels, rec,internal,gradObj)
        else:
            cache = self._caches.setdefault('rasterData', {'fn': '_addRasterRecord', 'data': []})
            cache['data'].append((pxlData, channels, rec,internal,gradObj))

    def AddRasterImageLayer(self, pxlData, channels, exts):

        id = GeometryGLScene.getNextId()

        rec = RasterLayerRecord(id, exts=exts)
        self._loadRasterLayer(pxlData, channels, rec)

        return id

    def AddRasterIndexedLayer(self,pxlData,channels,exts,internal=None,gradObj=GradientRecord()):
        id = GeometryGLScene.getNextId()

        rec = RasterIndexLayerRecord(id,exts=exts)
        self._loadRasterLayer(pxlData,channels,rec,internal,gradObj)
        return id

    def AddReferenceLayer(self, srcLayerId, pureAlias=False):
        """ Placeholder for a record being maintained by another instance.

        Args:
            srcLayer (LayerRecord):

        Returns:
            int: id of reference record
        """
        id = GeometryGLScene.getNextId()
        rec = ReferenceRecord(id, self._layers[srcLayerId], pureAlias)
        self._loadReferenceLayer(rec)
        return id

    def _typeSetForRec(self, rec):

        if isinstance(rec, ReferenceRecord):
            rec = rec.srcRecord

        if isinstance(rec, PolyLayerRecord):
            return self._polyLayerIds
        elif isinstance(rec, PointLayerRecord):
            return self._pointLayerIds
        elif isinstance(rec, LineLayerRecord):
            return self._lineLayerIds
        elif isinstance(rec, RasterLayerRecord):
            return self._rasterLayerIds

        raise ValueError("unknown layer type: {}".format(type(rec).__name__))

    # <editor-fold desc="Data Loading on Add">
    def _LoadGLBuffer(self, verts, ext, rec, extra=None):
        """Load vertex data into GPU memory, adjusting extents as necessary.

        Args:
            verts (numpy.array): 1D array of float values representing ordered vertex components.
            ext (tuple): A list of values representing the minimum extent. Ignored if set to `None`.
            rec (LayerRecord): Reference to Vertex Array Object to populate.
            buff (int): Reference to Vertex Buffer Object to populate.

        Returns:

        """
        if ext is not None:
            self.SetMaxExtents(*ext)

        glBindVertexArray(rec.vao)
        # ??? Should we split into separate functions?

        glBindBuffer(GL_ARRAY_BUFFER, rec.buff)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

        drawMode = GL_STATIC_DRAW if not rec.volatile else GL_DYNAMIC_DRAW
        rec.loadGLBuffer(verts,drawMode,self,extra)

        glBindVertexArray(0)
        self.markFullRefresh()

    def _LoadTexture(self, vals, trgTex, texMode, channels, texLoc,internal=None,interp=False):
        """

        Args:
            vals ():
            texLoc ():

        Returns:

        """

        if internal is None:
            internal=channels
        if channels == GL_RED:
            cCount = 1
        elif channels == GL_RG:
            cCount = 2
        elif channels == GL_RGB or channels == GL_BGR:
            cCount = 3
        elif channels == GL_RGBA or channels == GL_BGRA:
            cCount = 4
        else:
            raise ValueError("Unsupported option for format: {}".format(channels))

        glActiveTexture(trgTex)
        glBindTexture(texMode, texLoc)
        glTexParameteri(texMode, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(texMode, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        filter = GL_NEAREST if not interp else GL_LINEAR
        glTexParameteri(texMode, GL_TEXTURE_MIN_FILTER, filter)
        glTexParameteri(texMode, GL_TEXTURE_MAG_FILTER, filter)

        if texMode == GL_TEXTURE_1D:
            w = vals.shape[0] // cCount
            glTexImage1D(texMode, 0, internal, w, 0, channels, GL_FLOAT, vals)

        elif texMode == GL_TEXTURE_2D:
            h, w = vals.shape[:2]
            if len(vals.shape) == 2:
                h //= cCount
                w //= cCount
            glTexImage2D(texMode, 0, internal, w, h, 0, channels, GL_FLOAT, vals.ravel())
            # elif len(vals.shape)==3:
        # ...
        else:
            raise ValueError('texMode of type "{}" not supported'.format(texMode))
        # ...
        # glGenerateMipmap(texMode)

    def UpdateIndexRasterGradient(self,id,gradObj,targetTex=1):

        lyr = self._layers[id]
        if not isinstance(lyr,RasterIndexLayerRecord):
            raise GaiaGLException(f"Cannot update gradient; layer {id} is not a RasterIndexLayerRecord")
        if lyr.gradTexId == 0:
            raise GaiaGLException(f"Layer {id} has no gradient assigned")

        # get standard width
        valbuff = np.array([0],dtype=np.int32)

        with self.grabContext():
            glBindTexture(GL_TEXTURE_1D, lyr.gradTexId)
            glGetTexLevelParameteriv(GL_TEXTURE_1D,0,GL_TEXTURE_WIDTH,valbuff)
            w=valbuff[0]
            data = gradObj.colorStrip(w,True)
            glActiveTexture(GL_TEXTURE0+targetTex)

            glTexSubImage1D(GL_TEXTURE_1D, 0, 0, w, GL_RGBA, GL_FLOAT, data)

        self.markFullRefresh()


    # </editor-fold>

    # </editor-fold>

    # <editor-fold desc="Delete Layers">
    def DeleteLayer(self, id):
        if id<0:
            return
        rec = self._layers[id]
        rec.ClearBuffers()
        self._drawStack.remove(rec)
        self._typeSetForRec(rec).remove(id)
        self._layers.pop(rec.id)
        self.markFullRefresh()

    def ClearPointSelections(self):

        for id in self._pointLayerIds:
            rec = self._layers[id]
            rec.selectedRecs.fill(0)
        self.markFullRefresh()

    def ClearPolySelections(self):

        for id in self._polyLayerIds:
            rec = self._layers[id]
            rec.selectedRecs.fill(0)
        self.markFullRefresh()

    def ClearLineSelections(self):

        for id in self._lineLayerIds:
            rec = self._layers[id]
            rec.selectedRecs.fill(0)
        self.markFullRefresh()

    def ClearLayerSelections(self):
        for rec in self._drawStack:
            rec.selectedRecs.fill(0)
        self.markFullRefresh()

    def ClearPolyLayers(self):
        idCache = tuple(self._polyLayerIds)
        for id in idCache:
            self.DeleteLayer(id)
        self.markFullRefresh()
        self._doRefresh()

    def ClearPointLayers(self):
        idCache = tuple(self._pointLayerIds)
        for id in idCache:
            self.DeleteLayer(id)
        self.markFullRefresh()
        self._doRefresh()

    def ClearLineLayers(self):
        idCache = tuple(self._lineLayerIds)
        for id in idCache:
            self.DeleteLayer(id)
        self.markFullRefresh()
        self._doRefresh()

    def ClearRasterLayers(self):
        idCache = tuple(self._rasterLayerIds)
        for id in idCache:
            self.DeleteLayer(id)
        self.markFullRefresh()
        self._doRefresh()

    def ClearAllLayers(self):
        idCache = tuple(self._pointLayerIds.union(self._polyLayerIds).union(self._lineLayerIds).union(self._rasterLayerIds))
        for id in idCache:
            self.DeleteLayer(id)
        self.markFullRefresh()
        self._doRefresh()

    # </editor-fold>

    # <editor-fold desc="Layer Property manipulators">
    def SetLayerFillPolys(self, id, doFill, useAttr=False):
        if id in self._polyLayerIds:
            self._layers[id].fillGrid = doFill
            self._layers[id].useFillAttrVals = useAttr
            self.markFullRefresh()
            self._doRefresh()

    def SetLayerAttrVals(self, id, aVals):
        if id in self._polyLayerIds:
            self._layers[id].attrVals = aVals
            self.markFullRefresh()
            self._doRefresh()

        # TODO: update for line layer

    def AllLayersFillPolys(self, doFill, useAttr=False):

        for id in self._polyLayerIds:
            self._layers[id].fillGrid = doFill
            self._layers[id].useFillAttrVals = useAttr
        self.markFullRefresh()
        self._doRefresh()

    def SetLayerDrawGrid(self, id, isVisible):
        if id in self._polyLayerIds:
            self._layers[id].drawGrid = isVisible
            self.markFullRefresh()
            self._doRefresh()

    def AllLayersDrawGrid(self, visible):

        for id in self._polyLayerIds:
            self._layers[id].drawGrid = visible
        self.markFullRefresh()
        self._doRefresh()

    def SetLayerVisible(self, id, isVisible):
        self._layers[id].draw = isVisible
        self.markFullRefresh()
        self._doRefresh()

    def GetLayerVisible(self, id):
        return self._layers[id].draw

    def AllPointLayersVisible(self, isVisible):
        for id in self._pointLayerIds:
            self._layers[id].draw = isVisible
        self.markFullRefresh()
        self._doRefresh()

    def AllPolyLayersVisible(self, isVisible):
        for id in self._polyLayerIds:
            self._layers[id].draw = isVisible
        self.markFullRefresh()
        self._doRefresh()

    def AllRasterLayersVisible(self, isVisible):
        for id in self._rasterLayerIds:
            self._layers[id].draw = isVisible
        self.markFullRefresh()
        self._doRefresh()

    # </editor-fold>

    # <editor-fold desc="Layer Selection methods">
    def layerIter(self):
        return self._layers.values()

    def UpdateLayerVertices(self, id, verts):
        """

        Args:
            id (int): Update vertices for an existing layer.
            verts (numpy.array): The new vertex positions.

        Notes:
            Count of vertices will not change; do not add more vertices than added in original layer.
            Works best if layer is marked as volatile
        """
        rec = self._layers[id]
        if isinstance(rec, ReferenceRecord):
            rec = rec.srcRecord

        with self.grabContext():
            glBindVertexArray(rec.vao)
            glBindBuffer(GL_ARRAY_BUFFER, rec.buff)
            glBufferSubData(GL_ARRAY_BUFFER, 0, verts.nbytes, verts)

        self.markFullRefresh()
        self._doRefresh()

    def GetLayer(self, id):
        return self._layers[id]

    def ToggleLayerSelect(self, layer, ind):

        rec = self._layers[layer]
        rec.selectedRecs[ind] = 0 if rec.selectedRecs[ind] == 1 else 1
        self.markFullRefresh()

    def SelectAllLayer(self, id, select):
        rec = self._layers[id]
        for i in range(len(rec.selectedRecs)):
            rec.selectedRecs[i] = int(select)

        self.markFullRefresh()

    def GetSelectedGeom(self, id):
        rec = self._layers[id]
        return tuple([i for i in range(len(rec.selectedRecs)) if rec.selectedRecs[i] == 1])

    # </editor-fold>

    # <editor-fold desc="Matrix Transformations">
    def ResetView(self):
        """Reset the view matrix back to the identity state."""
        self._viewMat = glm.mat4(1.)
        self._updateMVP()
        self.markFullRefresh()
        self._doRefresh()

    def DistanceForTranslate(self, start, finish):
        """Translate the view scene to reflect the delta between start and finish.

        A translation is an addition to the values in the rightmost column of a vector (minus the homogenous anchor):

        | 1  0  0  x + Tx |
        | 0  1  0  y + Ty |
        | 0  0  1  z + Tz |
        | 0  0  0  1      |

        Where T is the translation vector

        Args:
            start (list): 3-value vector containing 3D coordinates representing the start position.
            finish (list): 3-value vector containing 3D coordinates representing the finish position.

        """
        for i in range(3):
            bound = self._viewMat[0][0]
            self._viewMat[3][i] += finish[i] - start[i]
            if self._viewMat[3][i] < -bound:
                self._viewMat[3][i] = -bound
            elif self._viewMat[3][i] > bound:
                self._viewMat[3][i] = bound

        self._updateMVP()
        self.markFullRefresh()
        self._doRefresh()

        # diff = finish-start
        # diff.z = 0.
        # diff.w = 1.
        # self.TranslateTo(diff)

    def TranslateView(self, curr):
        """Translate the view scene to reflect the delta between start and finish.

        A translation is an addition to the values in the rightmost column of a vector (minus the homogenous anchor):

        | 1  0  0  Tx |
        | 0  1  0  Ty |
        | 0  0  1  Tz |
        | 0  0  0  1  |

        Where T is the translation vector

        Args:
            curr (list): 3-value vector containing  3D coordinates of new position.

        """
        for i in range(3):
            bound = self._viewMat[0][0]
            # dist = curr[i] - self._viewMat[3][i]
            self._viewMat[3][i] -= curr[i]
            if self._viewMat[3][i] < -bound:
                self._viewMat[3][i] = -bound
            elif self._viewMat[3][i] > bound:
                self._viewMat[3][i] = bound
        self._updateMVP()
        self.markFullRefresh()
        self._doRefresh()

    def TranslateViewTo(self, curr):
        """Translate the view scene to reflect the delta between start and finish.

        A translation is an addition to the values in the rightmost column of a vector (minus the homogenous anchor):

        | 1  0  0  Tx |
        | 0  1  0  Ty |
        | 0  0  1  Tz |
        | 0  0  0  1  |

        Where T is the translation vector

        Args:
            curr (list): 3-value vector containing  3D coordinates of new position.

        """
        for i in range(3):
            bound = self._viewMat[0][0]
            # dist = curr[i] - self._viewMat[3][i]
            self._viewMat[3][i] = curr[i]
            if self._viewMat[3][i] < -bound:
                self._viewMat[3][i] = -bound
            elif self._viewMat[3][i] > bound:
                self._viewMat[3][i] = bound
        self._updateMVP()
        self.markFullRefresh()
        self._doRefresh()

    def SetPosition(self, pos):
        """ Set the absolute position of a translation instead of applying it to the existing position.

        Overwriting the position of a matrix looks like this:

        | 1  0  0  Px |
        | 0  1  0  Py |
        | 0  0  1  Pz |
        | 0  0  0  1  |

        Where P is the new Position Vector.


        Args:
            pos (list): A 3-value position vector or a 4-value homogenous coordinate vector, representing the new position.

        """

        for i in range(3):
            self._viewMat[3, i] = pos[i]
        self._updateMVP()
        self.markFullRefresh()
        self._doRefresh()

    def SetPtSize(self, id, newSize):
        """Set the size to use when rendering points.

        Args:
            newSize (float): The size to use when rendering a point.
        """

        if id not in self._pointLayerIds:
            raise ValueError('Record {} is not a Point Layer'.format(id))
        with self.grabContext():
            self._layers[id].ptSize = newSize
        self.markFullRefresh()
        self._doRefresh()

    def SetPtGlyph(self, id, glyph):
        """

        Args:
            id:
            glyph:

        Returns:

        """

        if id not in self._pointLayerIds:
            raise ValueError('Record {} is not a Point Layer'.format(id))
        self._layers[id].glyphCode = glyph
        self.markFullRefresh()
        self._doRefresh()

    def IncrementZoom(self, zoomIn, stepSize=None):
        """ Zoom the view in or out.

        "Zooming" is really applying a scale operation to the view matrix, which looks like this:

        | Sx 0  0  0  |
        | 0  Sy 0  0  |
        | 0  0  Sz 0  |
        | 0  0  0  1  |

        Where S is the scaling vector.

        Note that the translation values are also modified to keep the scene properly centered when zooming.

        Args:
            zoomIn (bool): Zoom in if true; zoom out if false.
            stepSize (float): The distance to zoom per increment.

        """
        if stepSize is None or stepSize < 0:
            stepSize = 1

        dir = 1 if zoomIn else -1
        oldZoom = float(self._viewMat[0][0])
        self._zoomLevel += dir * stepSize
        if self._zoomLevel < 0:
            self._zoomLevel = 0

        self._viewMat[0][0] = self._viewMat[1][1] = self._viewMat[2][2] = 2**self._zoomLevel

        # adjust translate so we are still centered
        adj = self._viewMat[0][0] / oldZoom
        self._RepositionZoom(adj)

    def zoomToExts(self, left, right, bottom, top):

        # if self._initialized:
        lb = self._mvpMat * glm.vec4(left, bottom, 0., 1., )
        rt = self._mvpMat * glm.vec4(right, top, 0., 1., )

        center = (lb + rt) / 2
        wh = rt - lb
        if wh.xy == glm.vec2(0.):
            # 0-sized rec passed in; silently abort
            return
        asp = 2 / max(wh.x, wh.y)
        self.MultiplyZoom(asp)
        self.TranslateView(center)
        self._RepositionZoom(asp)

    # else:
    #     cache = self._caches.setdefault('zoomToExts', {'fn': 'zoomToExts', 'data': []})
    #     cache['data'].append((left,right,bottom,top))

    def zoomToRubberBand(self):

        if self.rb_p1 is not None and self.rb_p2 is not None:
            center = ((self.rb_p1 + self.rb_p2) / 2).xyz
            wh = glm.abs(self.rb_p2 - self.rb_p1)
            asp = 2 / min(wh.x, wh.y)
            # center*=-1
            self.MultiplyZoom(asp)
            self.TranslateView(center)
            self._RepositionZoom(asp)

            # self.zoomToExts(left,right,bottom,top)

    def _RepositionZoom(self, adj):
        """Recenter after zoom

        Args:
            adj (float): Ratio to use for recenter.

        """

        self._viewMat[3][0] *= adj
        self._viewMat[3][1] *= adj
        self._viewMat[3][2] *= adj
        self._updateMVP()
        self.markFullRefresh()
        self._doRefresh()

    def MultiplyZoom(self, zoom):
        """Multiply scale value by S.
        | Sx 0  0  0  |
        | 0  Sy 0  0  |
        | 0  0  Sz 0  |
        | 0  0  0  1  |


        Args:
            zoom (float): The factor to increase/decrease scale by ('S' in the above diagram)

        """

        self._viewMat[0][0] *= zoom
        self._viewMat[1][1] *= zoom
        self._viewMat[2][2] *= zoom
        self._updateMVP()
        self.markFullRefresh()
        self._doRefresh()

        if self._viewMat[0][0]>0:
            self._zoomLevel=np.log2(self._viewMat[0][0])
        else:
            self._zoomLevel=0

    def zoomToLayer(self, id):

        if id >= 0:
            rec = self._layers[id]
            self.zoomToExts(*rec.exts)

    def updateProjMat(self):

        if self._eRight is None or self._eLeft is None or self._eTop is None or self._eBottom is None:
            return
        width = float(self._eRight - self._eLeft)
        height = float(self._eTop - self._eBottom)

        extra_height = 0
        extra_width = 0
        if self._widthDominant:
            extra_height = ((height * self._offs_ratio) - height) / 2.
        else:
            extra_width = ((width * self._offs_ratio) - width) / 2.

        # add in margins
        aleft = self._eLeft - (self._eMargin * width) - extra_width
        aright = self._eRight + (self._eMargin * width) + extra_width
        abottom = self._eBottom - (self._eMargin * height) - extra_height
        atop = self._eTop + (self._eMargin * height) + extra_height

        self._geomExts = (aleft, aright, abottom, atop)
        self._geomSize = (aright - aleft, atop - abottom)

        # calculate and store the orthographic projection matrix
        self.orthoMat = glm.ortho(*self._geomExts, 1., -1.0)

    def _updateMVP(self):
        """Update the cached MVP matrix and its inverse for use in rendering calculations."""

        vpMat = self._viewMat * self.orthoMat
        self._mvpMat = self._mdlMat * self._viewMat * self.orthoMat
        self._mvpInvMat = glm.inverse(self._mvpMat)

        self.refreshTextTransMat()

    # </editor-fold>

    # <editor-fold desc="Color methods">
    def _getRecordIdColor(self,recId,featInd=None):
        """ Get a color to represent the id (and feature id).
        Both recId and featInd are stored in 16 bit, meaning 65,536 unique values are supported for each field.

        Args:
            recId (int): The id for the layer.
            featInd (int,optional): The subfeature id of the layer.

        Returns:
            glm.vec4: The color to be used as an identifier during picking operations
        """
        rLower = np.float32((recId % 256) / 255.)
        rUpper = np.float32((recId >> 8) / 255.)

        fLower = 0.
        fUpper = 0.
        if featInd is not None:
            fLower = np.float32((featInd % 256) / 255.)
            fUpper = np.float32((featInd >> 8) / 255.)

        return glm.vec4(rLower, rUpper, fLower, fUpper)

    def _assignPolyFillColor(self, pickMode, rec, featInd):

        # assign the color for the current polygon.
        colorLoc = self._progMgr['inColor']
        if not pickMode:
            color = rec.geomColors[featInd]
        else:
            color = self._getRecordIdColor(rec.id,featInd)
        glUniform4fv(colorLoc, 1,glm.value_ptr(color))

    def layerColors(self, id):
        """list: Fill domainColors for each polygon listed in order; see the `fillColor` property for format of individual domainColors."""
        return self._layers[id].geomColors

    def SetColors(self, id, pcs):

        rec = self._layers[id]
        rec.geomColors = [glm.vec4(*x) for x in pcs]

        missing = len(rec.groups) - len(rec.geomColors)
        if missing > 0:
            rec.geomColors += [rec.geomColors[-1] for _ in range(missing)]
        self.markFullRefresh()
        self._doRefresh()

    def updateColor(self, id, color, index=None):

        if not isinstance(color, glm.vec4):
            color = glm.vec4(*color)
        rec = self._layers[id]
        if index is None:
            rec.setSingleColor(color)
        elif index < len(rec.geomColors):
            rec.geomColors[index] = color
        self.markFullRefresh()
        self._doRefresh()

    def updateGridColor(self, id, color):

        if not isinstance(color, glm.vec4):
            color = glm.vec4(*color)
        rec = self._layers[id]
        if isinstance(rec, PolyLayerRecord):
            rec.gridColor = color
            self.markFullRefresh()
            self._doRefresh()

    def updateFillGrid(self, id, doFill):

        rec = self._layers[id]
        if isinstance(rec, PolyLayerRecord):
            rec.fillGrid = doFill
            self.markFullRefresh()
            self._doRefresh()

    def updateLineThickness(self, id, thickness):

        rec = self._layers[id]
        if isinstance(rec, PolyLayerRecord) or isinstance(rec,LineLayerRecord):
            rec.line_thickness = thickness
            self.markFullRefresh()
            self._doRefresh()

    def updateGridThickness(self, id, thickness):
        # NOTE: This function is deprecated, use updateLineThickness() instead
        self.updateLineThickness(id,thickness)

    def updatePointSize(self, id, ptSize):

        rec = self._layers[id]
        if isinstance(rec, PointLayerRecord):
            rec.ptSize = ptSize
            self.markFullRefresh()
            self._doRefresh()

    def _updateRubberBandColor(self):
        with self.grabContext():
            self._progMgr.useProgram('rubberBand')
            glUniform4fv(self._progMgr['color1'],1,glm.value_ptr(self._rbColor1))
            glUniform4fv(self._progMgr['color2'], 1, glm.value_ptr(self._rbColor2))

    def _repackageIndexedColors(self, rec, dColor=glm.vec4(0., 0., 0., 1.)):
        expColors = IndexedColor.expandIndexes(rec.geomColors, rec.count, dColor)

        with self.grabContext():
            glBindVertexArray(rec.vao)

            glBindBuffer(GL_ARRAY_BUFFER, rec.auxColorBuff)
            glBufferSubData(GL_ARRAY_BUFFER, 0, expColors.nbytes, expColors)
            self.markFullRefresh()
            self._doRefresh()

    def replaceIndexColors(self, lyrid, iColors, dColor=glm.vec4(0., 0., 0., 1.)):

        rec = self._layers[lyrid]
        if getattr(rec, 'colorMode', None)!=POINT_FILL.INDEX:
            raise ValueError("layer does not use indexed color")
        rec.geomColors = iColors
        self._repackageIndexedColors(rec, dColor)

    def updateIndexColor(self, lyrid, index, color):

        rec = self._layers[lyrid]
        if getattr(rec, 'colorMode', None)!=POINT_FILL.INDEX:
            raise ValueError("layer does not use indexed color")
        if color != rec.geomColors[index].color:
            rec.geomColors[index].color = color

            self._repackageIndexedColors(rec)

    def setRasterSmoothing(self,lyrid,smooth):

        rec = self._layers[lyrid]
        if not isinstance(rec,RasterLayerRecord):
            # do nothing
            return
        if rec.smooth != smooth:
            filterMode = GL_LINEAR if smooth else GL_NEAREST
            texMode = GL_TEXTURE_2D
            glBindTexture(texMode, rec.texId)
            glTexParameteri(texMode, GL_TEXTURE_MIN_FILTER, filterMode)
            glTexParameteri(texMode, GL_TEXTURE_MAG_FILTER, filterMode)
            rec.smooth = smooth
            self.markFullRefresh()

    def setIndexRasterValueBoundaries(self,lyrid,low=0.,high=1.):
        """ low,high should be [0.,1.]

        Args:
            lyrid:
            low:
            high:

        """

        rec = self._layers[lyrid]
        if not (isinstance(rec, RasterIndexLayerRecord) or isinstance(rec,PointLayerRecord)):
            # do nothing
            return

        if rec.lowVal != low or rec.highVal != high:
            rec.lowVal= low
            rec.highVal= high
            self.markFullRefresh()


    def setIndexClampGradient(self,lyrid,doClamp):
        rec = self._layers[lyrid]
        if not (isinstance(rec, RasterIndexLayerRecord) or isinstance(rec,PointLayerRecord)):
            # do nothing
            return

        if rec.clampColorToRange != doClamp:
            rec.clampColorToRange = doClamp
            self.markFullRefresh()

    # </editor-fold>

    # <editor-fold desc="Cleanup Methods">
    def clearUtilityBuffers(self):

        if bool(glDeleteBuffers):
            if any([self._gFillBuff, self._rbBuff, self._axesBuff]):
                glDeleteBuffers(3, [self._gFillBuff, self._rbBuff, self._axesBuff])
            if any([self._gFillVao, self._rbVao, self._axesVao]):
                glDeleteVertexArrays(3, [self._gFillVao, self._rbVao, self._axesVao])

        # TODO: add text/atlas cleanup here

    def cleanupOpenGL(self):

        try:
            with self.grabContext():
                self.ClearAllLayers()
                self.clearUtilityBuffers()
                if self._initialized:
                    self._progMgr.cleanup()
        except ImportError:
            # this triggers sometimes when the state is shutting down under debug
            pass

    # </editor-fold>

    # <editor-fold desc="Picking and rubberband">
    def doMousePick(self, x, y):

        if self.allowPicking:

            with self.grabContext():
                # glReadBuffer(GL_BACK)

                glViewport(*self._dims)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

                # load and assign base shader program.
                self._progMgr.useProgram('simple')
                glUniformMatrix4fv(self._progMgr['mvpMat'], 1, GL_FALSE, glm.value_ptr(self._mvpMat))

                for rec in reversed(self._drawStack):

                    if isinstance(rec, PolyLayerRecord) and self._allowPolyPicking:
                        self._drawPolyLayer(rec, True)
                    elif isinstance(rec, PointLayerRecord) and self._allowPtPicking:
                        self._drawPointLayer(rec, True)
                    if isinstance(rec, LineLayerRecord) and self._allowLinePicking:
                        self._drawLineLayer(rec, True)

                glFlush()
                glFinish()

                # glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
                # glPixelStorei(GL_PACK_ALIGNMENT, 1)
                lyLower, lyUpper, recLower, recUpper = glReadPixels(x, self._dims[3] - y, 1, 1, GL_RGBA, GL_FLOAT)[0][0]

            # raw = glReadPixels(x,y,1,1,GL_RG,GL_FLOAT)

            if lyLower == 1. and lyUpper == 1. and recLower == 1. and recUpper == 1.:
                # miss
                return None

            layer = int(255 * lyLower) + (int((lyUpper * 255)) << 8)
            group = int(255 * recLower) + (int((recUpper * 255)) << 8)

            return layer, group

        return None

    def _UpdateSelections(self, index):

        lyr = self._layers[index]
        if isinstance(lyr, PointLayerRecord):
            # TODO: update below to be for a more general case
            glBindVertexArray(lyr.vao)
            glBindBuffer(GL_ARRAY_BUFFER, lyr.ptSelBuff)
            glBufferSubData(GL_ARRAY_BUFFER, 0, lyr.selectedRecs.nbytes, lyr.selectedRecs)
            glBindBuffer(GL_ARRAY_BUFFER, lyr.buff)
            glBindVertexArray(0)

    def updateRubberBand(self, p1, p2):

        if self._initialized:
            self.rb_p1 = p1
            self.rb_p2 = p2
            if p1 is not None and p2 is not None:
                verts = np.array([p1[0], p1[1],
                                  p1[0], p2[1],
                                  p2[0], p2[1],
                                  p2[0], p1[1]], dtype=np.float32)

                with self.grabContext():
                    glBindVertexArray(self._rbVao)
                    glBindBuffer(GL_ARRAY_BUFFER, self._rbBuff)
                    glBufferSubData(GL_ARRAY_BUFFER, 0, verts.nbytes, verts)
                    glBindVertexArray(0)

    def WorldPointToScene(self, pt):
        """ Perform a reverse-point lookup on the scene

        Args:
            pt (object): A container with at least two indexed values in the range of [-1,1]

        Returns:
            numpy.ndarray: The four-component homogenous coordinate from the scene
        """
        h_pt = glm.vec4(pt[0], pt[1], 0, 1)

        return self._mvpInvMat * h_pt

    def ScenePointToWorld(self, pt):

        h_pt = glm.vec4(pt[0], pt[1], 0, 1)

        return self._mvpMat * h_pt

    # </editor-fold>

    # <editor-fold desc="Texture management">
    def SetReferenceTexture(self, layerId, vals, refExts, oobColor=np.array([1., 1., 0., 1.], dtype=np.float32)):
        """ Set 2D texture with values referenced from GIS operation

        Args:
            vals (numpy.array): 2D array of pixel values.
            minmax (tuple): tuple with min, max values.

        """

        if self._initialized:

            if layerId not in self._polyLayerIds:
                raise ValueError('Record {} is not a polygon layer.'.format(layerId))
            layer = self._layers[layerId]

            # remove old, if any
            glDeleteTextures(1, [layer.refTex])
            glDeleteVertexArrays(1, [layer.refVao])
            glDeleteBuffers(1, [layer.refBuff])

            layer.refTex = glGenTextures(1)
            layer.refVao = glGenVertexArrays(1)
            layer.refBuff = glGenBuffers(1)

            valMin = vals.min()
            valMax = vals.max()

            # build surface for texture
            glBindVertexArray(layer.refVao)
            glBindBuffer(GL_ARRAY_BUFFER, layer.refBuff)

            minX, maxX, minY, maxY = layer.exts
            rMinX, rMaxX, rMinY, rMaxY = refExts
            minS = (minX - rMinX) / (rMaxX - rMinX)
            maxS = (maxX - rMinX) / (rMaxX - rMinX)
            minT = (minY - rMinY) / (rMaxY - rMinY)
            maxT = (maxY - rMinY) / (rMaxY - rMinY)
            # minS = 0.
            # maxS = 1.
            # minT = 0.
            # maxT = 1.
            fill = np.array([minX, maxY, minS, maxT,
                             minX, minY, minS, minT,
                             maxX, maxY, maxS, maxT,
                             maxX, minY, maxS, minT, ], dtype=np.float32)

            glEnableVertexAttribArray(0)
            glEnableVertexAttribArray(1)
            step = 16  # four float32 s
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, step, None)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, step, ctypes.c_void_p(8))
            glBufferData(GL_ARRAY_BUFFER, fill.nbytes, fill, GL_STATIC_DRAW)

            # normalize data
            transVals = (vals - valMin) / (valMax - valMin)
            self._LoadTexture(transVals, GL_TEXTURE0, GL_TEXTURE_2D, GL_RED, layer.refTex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, oobColor)

            # layer.fillMode = POLY_FILL.VAL_REF
            self.markFullRefresh()
        else:
            cache = self._caches.setdefault('refTex', {'fn': 'SetReferenceTexture', 'data': []})
            cache['data'].append((layerId, vals, refExts))

    def SetGradientTexture(self, layerId, gradObj, forRefTex=True):
        """ Create 1D texture containing gradient colors and refs.

        Args:
            gradObj ():

        Returns:

        """

        GRAD_WIDTH = 64

        if isinstance(gradObj, GradientRecord):
            if self._initialized:

                isUpdate = False
                layer = self._layers[layerId]

                with self.grabContext():
                    if layerId in self._polyLayerIds:
                        ind = POLY_GRAD_IND.REF if forRefTex else POLY_GRAD_IND.VAL
                        if layer.customGradTexes[ind]==0:
                            layer.customGradTexes[ind] = glGenTextures(1)
                        else:
                            isUpdate = True
                        tId = layer.customGradTexes[ind]
                    elif layerId in self._pointLayerIds or layerId in self._lineLayerIds:

                        # since gradient texture, we can reuse
                        if layer.gradTexId == 0:
                            layer.gradTexId = glGenTextures(1)
                        else:
                            isUpdate=True
                        tId = layer.gradTexId
                    else:
                        raise ValueError('Record {} is not a polygon or point layer.'.format(layerId))
                    # if forRefTex and layer.refVao == 0:
                    #     raise Exception("No reference texture defined")

                    texTarg = GL_TEXTURE1 if forRefTex else GL_TEXTURE2
                    if not isUpdate:
                        self._LoadTexture(gradObj.colorStrip(GRAD_WIDTH, True), texTarg, GL_TEXTURE_1D, GL_RGBA,
                                          tId,interp=True)
                        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

                    else:
                        glActiveTexture(texTarg)
                        glBindTexture(GL_TEXTURE_1D, tId)
                        glTexSubImage1D(GL_TEXTURE_1D, 0, 0, GRAD_WIDTH, GL_RGBA, GL_FLOAT, gradObj.colorStrip(GRAD_WIDTH, True))

                self.markFullRefresh()
            else:
                cache = self._caches.setdefault('gradTex', {'fn': 'SetGradientTexture', 'data': []})
                cache['data'].append((layerId, gradObj, forRefTex))

        else:  # int
            lyr=self._layers[layerId]
            if isinstance(lyr,PolyLayerRecord):
                ind = POLY_GRAD_IND.REF if forRefTex else POLY_GRAD_IND.VAL
                lyr.customGradTexes[ind] = gradObj
            elif isinstance(lyr,PointLayerRecord):
                lyr.gradTexId = gradObj
            self.markFullRefresh()

    def SetPolyLayerFillMode(self, id, pfMode):
        if id in self._polyLayerIds:
            self._layers[id].fillMode = pfMode
            self.markFullRefresh()
            self._doRefresh()

    # </editor-fold>

    # <editor-fold desc="Drawstack Manipulators">
    def moveUpStack(self, id):
        if id<0:
            return
        rec = self._layers[id]
        loc = self._drawStack.index(rec)
        if loc >= 0:
            nextLoc = loc - 1
            swpRec = self._drawStack[nextLoc]
            self._drawStack[nextLoc] = rec
            self._drawStack[loc] = swpRec
            self.markFullRefresh()
            self._doRefresh()

    def moveDownStack(self, id):
        if id<0:
            return
        rec = self._layers[id]
        loc = self._drawStack.index(rec)
        nextLoc = loc + 1
        if len(self._drawStack) > nextLoc:
            swpRec = self._drawStack[nextLoc]
            self._drawStack[nextLoc] = rec
            self._drawStack[loc] = swpRec
            self.markFullRefresh()
            self._doRefresh()

    def moveTopStack(self, id):
        if id<0:
            return
        rec = self._layers[id]
        self._drawStack.remove(rec)
        self._drawStack.insert(0, rec)

    def moveBottomStack(self, id):
        if id<0:
            return
        rec = self._layers[id]
        self._drawStack.remove(rec)
        self._drawStack.insert(len(self._drawStack), rec)

    def getDrawStackPosition(self, id):
        return self._drawStack.index(self._layers[id])

    def setDrawStackPosition(self, id, pos):
        oldLoc = self.getDrawStackPosition(id)

        rec = self._drawStack.pop(oldLoc)
        if pos > oldLoc:
            pos -= 1
        self._drawStack.insert(pos, rec)

    # </editor-fold>

    # <editor-fold desc="Text and Axes">
    @staticmethod
    def _genNumberLabel(val, limit=10):

        ret = str(val)
        if len(ret) > limit:
            ret = f'{val:.{limit - 6}e}'
        return ret

    def _CreateAxes(self, minX, maxX, minY, maxY, tickWidth):

        self._prepTextEngine()

        flipXY = glm.mat4()
        flipXY[0][0] = -1
        # flipXY[0][0] = -1
        warpMat = glm.inverse(self._textProjMat) * flipXY * self.orthoMat
        tminX, tminY, _, _ = warpMat * glm.vec4(minX, minY, 0., 1.)
        tmaxX, tmaxY, _, _ = warpMat * glm.vec4(maxX, maxY, 0., 1.)

        if self._axesVao != 0:
            glBindVertexArray(self._axesVao)
        else:
            self._axesVao = glGenVertexArrays(1)
            self._axesBuff = glGenBuffers(1)
            glBindVertexArray(self._axesVao)
            glBindBuffer(GL_ARRAY_BUFFER, self._axesBuff)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
            glBufferData(GL_ARRAY_BUFFER, 32, None, GL_STATIC_DRAW)

        verts = np.array([
            # vertical axis
            tminX, tminY,
            tminX, tmaxY,

            # horizontal axis
            tminX, tminY,
            tmaxX, tminY,
        ], dtype=np.float32)
        self._progMgr.useProgram('axes')
        glUniform1f(self.progMgr['capTickWidth'], tickWidth)

        self._progMgr.useProgram()
        glBufferSubData(GL_ARRAY_BUFFER, 0, verts.nbytes, verts)
        glBindVertexArray(0)

        def genYLbl(x, y, val):
            xlbl = GeometryGLScene._genNumberLabel(val)
            xW, xH = self._txtRdr.renderSize(xlbl)
            pt = glm.vec4(x - xW - self._txtPtSize, y - (xH // 2), 0., 1.)
            return (pt, xlbl, (x, y))

        def genXLbl(x, y, val):
            ylbl = GeometryGLScene._genNumberLabel(val)
            yW, yH = self._txtRdr.renderSize(ylbl)
            pt = glm.vec4(x - (yW // 2), y - yH * 2, 0., 1.)
            return (pt, ylbl, (x, y))

        lbls = [genYLbl(tminX, tminY, maxY),
                genYLbl(tminX, tmaxY, minY),
                genXLbl(tminX, tminY, minX),
                genXLbl(tmaxX, tminY, maxX), ]

        self._strVertCount = self._txtRdr.loadStrings(self._atlasVao, self._stringBuff, lbls)

        self.axesTickCount = self._axTickCount

    def _prepTextEngine(self):
        """ Creates Txt Renderer if needed. This function should be called
        in any function that uses _txtRdr, whose initialization is JIT to
        avoid importing dependencies that are optional (ie freetype).

        """

        if self._txtRdr is None:
            self._txtRdr = TxtRenderer(self._txtFontPath, self._txtPtSize)
            # initialize text stuff
            self._atlasVao = glGenVertexArrays(1)
            self._stringBuff = glGenBuffers(1)
            self._atlasTex = glGenTextures(1)
            self._txtRdr.initGL(self._atlasVao, self._atlasTex, GL_TEXTURE3)

            glBindVertexArray(self._atlasVao)
            # TxtRenderer.PrepTextBuffer(self._atlasVao, self._stringBuff)


    # def getScreenExts(self):
    #
    #     left,bottom = glm.unProject(glm.vec3(0,0,0),self._viewMat,self.orthoMat,self._dims).xy
    #     right,top = glm.unProject(glm.vec3(self._dims[2],self._dims[3],0),self._viewMat,self.orthoMat,self._dims).xy
    #
    #     return [left,right,bottom,top]

    def updateScreenAspect(self, aspect):
        """

        Args:
            aspect (float): height / width, in pixels.

        """

        thickProg = self._progMgr.progLookup('thickline')
        if thickProg != 0:
            self._progMgr.useProgramDirectly(thickProg)
            glUniformMatrix2fv(self._progMgr['aspectMat'], 1, GL_FALSE, np.array([1., 0., .0, 1 / aspect],dtype=np.float32))

    def refreshTextTransMat(self):

        # try this
        self._txtTransMat[3][0] = self._viewMat[0][0] * self._viewMat[3][0]
        self._txtTransMat[3][1] = self._viewMat[1][1] * self._viewMat[3][1]
        self._txtTransMat[3][2] = self._viewMat[2][2] * self._viewMat[3][2]

    # </editor-fold>

    # <editor-fold desc="Binary caching">
    # BINARY IO Stuff (may want to move out of scene)
    TEXHEAD_DT = np.dtype([('width', '<u4'), ('height', '<u4'), ('internal', '<u4'), ('floats', '<u4')])

    def dumpVertsToStream(self, rec, strm):
        from .LayerCaching import GaiaGLCacheException
        if self._initialized:
            with self.grabContext():
                if not isinstance(rec, LayerRecord):
                    rec = self._layers[id]
                glBindVertexArray(rec.vao)
                glBindBuffer(GL_ARRAY_BUFFER, rec.buff)
                bytecount = 0
                if isinstance(rec, PolyLayerRecord):
                    # write the verts and norms at same time
                    bytecount = rec.vertCount * np.dtype(np.float32).itemsize * 2
                elif isinstance(rec, PointLayerRecord):
                    bytecount = rec.vertCount * np.dtype(np.float32).itemsize * 2
                elif isinstance(rec, LineLayerRecord):
                    bytecount = rec.vertCount * np.dtype(np.float32).itemsize * 2
                outVerts = glGetBufferSubData(GL_ARRAY_BUFFER, 0, bytecount)
                strm.write(outVerts)
                glBindVertexArray(0)
        else:
            if isinstance(rec, PolyLayerRecord):
                caches = self._caches['polyData']
                for verts, _, trgRec in caches['data']:
                    if rec is trgRec:
                        strm.write(verts.tobytes())
                        return
                # if we get here, error
                raise GaiaGLCacheException(f"Cannot find data for targetted polygon record {rec.id}")
            elif isinstance(rec, PointLayerRecord):
                caches = self._caches['ptData']
                for verts, _, trgRec,_ in caches['data']:
                    if rec is trgRec:
                        strm.write(verts.tobytes())
                        return
                # if we get here, error
                raise GaiaGLCacheException(f"Cannot find data for targetted point record {rec.id}")
            elif isinstance(rec, LineLayerRecord):
                caches = self._caches['lineData']
                for verts, _, trgRec,_ in caches['data']:
                    if rec is trgRec:
                        strm.write(verts.tobytes())
                        return
                # if we get here, error
                raise GaiaGLCacheException(f"Cannot find data for targetted line record {rec.id}")
            else:
                raise GaiaGLCacheException(f"Unsupported record type for caching: {type(rec)}")

    def dumpBuffToStream(self,buffType,vao,buff,nbytes,strm,offset=0):

        if self._initialized:
            with self.grabContext():
                glBindVertexArray(vao)
                glBindBuffer(buffType, buff)
                outVals = glGetBufferSubData(buffType, offset, nbytes)
                strm.write(outVals)
                glBindVertexArray(0)
        else:
            from .LayerCaching import GaiaGLCacheException
            raise GaiaGLCacheException("dumpBuffToStream() only works if scene is initialized.")

    def dumpTexToStream(self, rec, strm):

        with self.grabContext():
            glBindVertexArray(rec.vao)
            glBindBuffer(GL_ARRAY_BUFFER, rec.buff)
            dimBuff = np.zeros(1, dtype=np.int32)
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH, dimBuff)
            width = dimBuff[0]
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_HEIGHT, dimBuff)
            height = dimBuff[0]
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_RED_SIZE, dimBuff)
            rSize = dimBuff[0]
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_GREEN_SIZE, dimBuff)
            gSize = dimBuff[0]
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_BLUE_SIZE, dimBuff)
            bSize = dimBuff[0]
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_ALPHA_SIZE, dimBuff)
            aSize = dimBuff[0]

            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_INTERNAL_FORMAT, dimBuff)
            internalFormat = dimBuff[0]

            bytecount = ((rSize + gSize + bSize + aSize) // 8) * width * height

            strm.write(np.array([(width, height, internalFormat, bytecount)], dtype=GeometryGLScene.TEXHEAD_DT).tobytes())
            strm.write(glGetTexImage(GL_TEXTURE_2D, 0, internalFormat, GL_FLOAT))
            glBindVertexArray(0)


    def loadTexFromStream(self, strm,skip=False):

        buff = np.fromfile(strm, GeometryGLScene.TEXHEAD_DT, 1)
        width = int(buff['width'])
        height = int(buff['height'])
        internal = GLint(buff['internal'])
        floatcount = int(buff['floats'])

        if not skip:
            buff = np.fromfile(strm, np.float32, floatcount)
            pxdata = buff.reshape([width, height, floatcount % (width * height)])
        else:
            strm.seek(np.float32.itemsize*floatcount,whence=1)
            internal = None
            pxdata = None
        return internal, pxdata

    # </editor-fold>
