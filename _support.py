"""Support classes for renderers

"""
import sys
from enum import IntEnum

import glm
import numpy as np
from OpenGL.GL import *

from .textrenderer import StringEntry

# <editor-fold desc="Color classes">
# use intEnum to ensure caching values are consistant
# reserve 0 for noval
POLY_FILL = IntEnum('POLY_FILL','SOLID VAL_REF TEX_REF',start=1)
POINT_FILL = IntEnum('POINT_FILL','SINGLE INDEX GROUP VAL_REF',start=1)
LINE_FILL = IntEnum('LINE_FILL','SINGLE INDEX VAL_REF',start=1)
##########################################################
## Gradient Record class
##
## Since most rasters are for values and not direct
## display, it is worth having a lookup swatch. This
## is what the gradient lookup is intended for.
##########################################################
class GradientRecord(object):
    """Record for representing a gradient swatch with two or more anchor points.
    """

    def __init__(self,*args):
        self._weighted_colors = {0.0: glm.vec4(0., 0., 0., 1.),
                                 1.0: glm.vec4(1.,1.,1.,1.)}

        for wt,color in args:
            self.addColorAnchor(wt,color)

    def __setitem__(self, key, value):

        self._weighted_colors[float(key)] = glm.vec4(value)

    def __getitem__(self, weight):
        return self.colorForWeight(weight)

    def __iter__(self):

        for k in sorted(self._weighted_colors.keys()):
            yield k,self._weighted_colors[k]

    def __reversed__(self):

        for k in sorted(self._weighted_colors.keys(), reverse=True):
            yield k,self._weighted_colors[k]

    def __len__(self):
        return len(self._weighted_colors)

    def __eq__(self,other):
        return self._weighted_colors == other._weighted_colors

    def clear(self):
        """Clear all entries."""
        self._weighted_colors.clear()

    @staticmethod
    def _lerp(c1,c2,w):
        """Basic linear interpolation algorithm.

        Args:
            c1 (SimpleColor): The first color.
            c2 (SimpleColor): The second color.
            w (float): Normalized weight balancing c1 and c2.

        Returns:
            SimpleColor: The interpolated color value.
        """
        return (c1*(1.-w)) + (c2*w)

    def addColorAnchor(self,weight,color):
        """Add another anchor to the gradient.

        Args:
            weight (float): Normalized weight for location along gradient.
            color (iterable): The 4-channel color to insert at the anchor point.
        """
        self._weighted_colors[weight] = glm.vec4(color)

    def popColorAnchor(self,weight):
        """Remove and return a color.

        Args:
            weight (float): Normalized weight of color anchor.

        Returns:
            SimpleColor: The color at the anchor point.

        Raises:
             KeyError: If weight is not an anchor point.
        """
        return self._weighted_colors.pop(weight)

    def moveColorAnchor(self,oldWeight,newWeight):
        """ Move a color to a new anchor point.

        Args:
            oldWeight (float): The old anchor location.
            newWeight (float): the new location for the color.

        Raises:
            KeyError: If oldWeight is not an anchor point.
        """

        c = self.popColorAnchor(oldWeight)
        self.addColorAnchor(newWeight,c)


    def colorForWeight(self,weight):
        """Retrieve the color for the requested weight.

        Args:
            weight (float): Normalized weight value.

        Returns:
            SimpleColor: Color found at weight point.
            None: If no weighted colors are present.
        """

        if len(self._weighted_colors)==0:
            return None

        # clamp to [0,1]
        if weight < 0:
            weight = 0.
        elif weight > 1:
            weight = 1.

        lower=None
        upper=None

        # find bounds for interpolation
        for w,c in self:
            if lower is None and weight > w:
                lower = (w,c)
            elif weight <= w:
                upper = (w,c)

            if upper is not None:
                break

        # clamp color if no lower or upper bounds
        if lower is None:
            return next(iter(self))[1]
        if upper is None:
            return next(reversed(self))[1]

        #find the relative weight
        rel_wt = (weight-lower[0])/(upper[0]-lower[0])

        return GradientRecord._lerp(lower[1],upper[1],rel_wt)

    def colorStrip(self,count,flatten=False):
        """Builds a regular color strip based on weighted values

        Args:
            count (int): The number samples to take between 0 and 1.
            flatten (bool): If true, strings the individual channel values together
              in a fashion suitable for direct rendering. Defaults to false.
        Returns:
            list: If `flatten` is `False`; list of `SimpleColor` objects representing regular sampling
            numpy.array: If `flatten` is `True`; individual channel values for each color.
        """

        interval = 1. / (count-1.)
        counter = 0

        itr = iter(self)
        lower = None
        upper = next(itr)
        outlist = np.empty([count*4],dtype=np.float32)
        i=0
        while counter <= 1.:

            if counter >= upper[0]:
                lower = upper
                try:
                    upper = next(itr)
                except StopIteration:
                    upper = None

            if lower is None:
                outlist[i:i+4]=upper[1]
            elif upper is None:
                outlist[i:i+4]=lower[1]
            else:
                rel_wt=(counter-lower[0])/(upper[0]-lower[0])
                outlist[i:i+4]=GradientRecord._lerp(lower[1],upper[1],rel_wt)

            counter+=interval
            i+=4

        outlist = np.array(outlist,np.float32)
        if not flatten:
            outlist=outlist.reshape([outlist.shape[0]//4,4])
        return outlist

    def squeezeBetweenWeights(self,minWt,maxWt):
        """Squeeze current gradient between range of weights,  saturating with weighted values outside of range.

        Args:
            minWt (float): The lower bound weight in range (0,1); must be less than `maxWt`.
            maxWt (float): The upper bound weight in range (0,1); must be greater than `minWt`.
        """

        # debug assertions
        assert 0<=minWt<=1, 'minWt is outside of [0,1]'
        assert 0<=maxWt<=1, 'maxWt is outside of [0,1]'
        assert minWt<maxWt, 'minWt greater than maxWt'

        wtRange=maxWt-minWt

        # set min wt max wt to same colors as 0,1 to flatten ends
        newAnchors = {
                      minWt: self._weighted_colors[0.],
                      maxWt: self._weighted_colors[1.],
                      0.:self._weighted_colors.pop(0.),
                      1.:self._weighted_colors.pop(1.),
                      }

        # renormalize the rest to equivalent between min and max wts
        for wt,color in self._weighted_colors.items():
            newWt = (wt*wtRange)+minWt
            newAnchors[newWt] = color
        self._weighted_colors = newAnchors


    def inflateBetweenWeights(self,minWt,maxWt):
        """Stretch subrange of gradient to entire range, overwriting any anchors outside of the range.

        Args:
            minWt (float): The lower bound weight in range (0,1); must be less than `maxWt`.
            maxWt (float): The upper bound weight in range (0,1); must be greater than `minWt`.

        """

        # debug assertions
        assert 0 <= minWt <= 1, 'minWt is outside of [0,1]'
        assert 0 <= maxWt <= 1, 'maxWt is outside of [0,1]'
        assert minWt < maxWt, 'minWt greater than maxWt'

        wtRange = maxWt-minWt
        # renormalize anchors, discarding any outside of range
        newAnchors = {0:self.colorForWeight(minWt),
                      1:self.colorForWeight(maxWt),
                      }
        for wt,color in self._weighted_colors.items():
            if minWt < wt < maxWt:
                newWt= (wt-minWt)/wtRange
                newAnchors[newWt]=color
        self._weighted_colors = newAnchors


    def clone(self,squeeze=None,inflate=None,alphaOverride=None):
        """Creating a copy of the GradientRecord object, optionally transforming via squeeze or inflate.

        Args:
            squeeze (tuple,optional): Pair of lower and upper weights to apply in a squeeze transformation.
            inflate (tuple,optional): Pair of lower and upper weights to apply in an inflate transformation.
            alphaOverride (float or None, optional): Alpha value to apply to clone if not `None`.
        Returns:
            GradientRecord: Copy of GradientRecord with transformation applied.

        Notes:
            If both `squeeze` and `inflate` are passed in, The squeeze transformation will be applied first, followed
            by the inflate transformation.

        See Also:
            GradientRecord.squeezeBetweenWeights()
            GradientRecord.inflateBetweenWeights()
        """

        ret = GradientRecord()
        if alphaOverride is None:
            ret._weighted_colors=self._weighted_colors.copy()
        else:
            ret._weighted_colors.clear()
            for wt,c in self._weighted_colors.items():
                ret._weighted_colors[wt]=glm.vec4(c.rgb,alphaOverride)

        if squeeze is not None:
            ret.squeezeBetweenWeights(*squeeze)
        if inflate is not None:
            ret.inflateBetweenWeights(*inflate)
        return ret


class ColorRange(object):
    """ Record for coloring groups of vertices.

    Attributes:
        color (glm.vec4): Color range.
        start (int): The first index for applying color.
        count (int): The number of vertices to apply the color to.

    Args:
        color (glm.vec4): Color range.
        start (int): The first index for applying color.
        count (int): The number of vertices to apply the color to.
    """

    def __init__(self,color,start,count):
        self.color=glm.vec4(color)
        self.start = start
        self.count = count

    def __eq__(self,other):
        return self.color == other.color and \
               self.start == other.start and \
               self.count == other.count

class IndexedColor(object):
    """ Color associated with index.

    Attributes:
        color (glm.vec4): The color value.
        inds (list): The associated indexes.

    Args:
        color (glm.vec4): The color value.
        inds (list): The associated indexes.
    """

    @staticmethod
    def expandIndexes(indexes,recCount,d_color=glm.vec4(0.,0.,0.,1.)):
        """ Retrieve colors based on indices.

        Args:
            indexes (list): Indexes to look up.
            recCount (int): The number of colors to produce.
            d_color (glm.vec4): The color to use as default, in the case the index
                isn't present.

        Returns:
            list: colors associated with indexes.
        """
        expColors = np.full([recCount, 4], d_color,dtype=np.float32)
        for ci in indexes:
            for i in ci.inds:
                expColors[i] = ci.color
        return expColors


    def __init__(self, color, inds):
        self.color = color
        self.inds = inds

    def __len__(self):
        return len(self.inds)

    def __eq__(self,other):
        return self.color == other.color and self.inds==other.inds

class IndexedGlyph(object):
    """Maps a series of indices to a character representing a glyph used to represent spactial points.

    Attributes:
        glyphVal (int): `ord` value of character representing glyph.
        inds (list): The list of indices indicating the point to apply the glyph to.

    Args:
        glyph (str or int): int (ord value) or single-character string representing the point glyph.
        inds (list): list of point indices that are represented by this glyph.

    """

    @staticmethod
    def expandIndexes(indexes, recCount, d_glyph='.'):
        """Expand individual index values into a full list glyph ord values.

        Args:
            indexes (list): List of IndexedGlyph objects.
            recCount (int): Total number of entries.
            d_glyph (int or str, optional): The default value for unreferenced indices.

        Returns:
            numpy.ndarray: A list of ord (int) values representing the glyph for each point.
        """

        expGlyphs = np.full([recCount], ord(d_glyph) if isinstance(d_glyph,str) else d_glyph, dtype=np.uint32)
        for ci in indexes:
            for i in ci.inds:
                expGlyphs[i] = ci.glyphVal
        return expGlyphs

    def __init__(self,glyph,inds):

        self.glyphVal= ord(glyph) if isinstance(glyph,str) else glyph
        self.inds=inds

    def __len__(self):
        return len(self.inds)

    def __eq__(self,other):
        return self.glyphVal == other.glyphVal and self.inds==other.inds

    @property
    def glyph(self):
        """str: single character string which represents the glyph."""
        return chr(self.glyphVal) if self.glyphVal is not None else ''

    @glyph.setter
    def glyph(self, value):
        self.glyphVal = ord(value) if value is not None else value

class IndexedScale(object):
    """Maps a series of indices to a specific scaling value to apply to points.

    Attributes:
        scale (float): The scale factor to apply to the associated indices.
        inds (list): The list of indices indicating the point to apply the glyph to.

    Args:
        scale (float): Scaling factor to apply.
        inds (list): list of point indices that are represented by this glyph.

    """

    @staticmethod
    def expandIndexes(indexes, recCount, d_scale=1):
        """Expand individual index values into a full list scaling factors

        Args:
            indexes (list): List of IndexedGlyph objects.
            recCount (int): Total number of entries.
            d_scale (float, optional): The default scaling factor for unreferenced indices.

        Returns:
            numpy.ndarray: A list of float values representing the scaling factor for each point.

        """

        expScales = np.full([recCount], d_scale, dtype=np.float32)
        for ci in indexes:
            for i in ci.inds:
                expScales[i] = ci.scale
        return expScales

    def __init__(self, scale, inds):
        self.scale = scale
        self.inds = inds

    def __len__(self):
        return len(self.inds)

    def __eq__(self, other):
        return self.scale == other.scale and self.inds == other.inds
# </editor-fold>


# <editor-fold desc="Layer Classes">
class LayerRecord(object):
    """ Record of draw data for a given "ogr_layer" of data.

    Attributes:
          vao (int): Vertex array object provided by the OpenGL API.
          buff (int): Array buffer provided by the OpenGL API.
          draw (bool): If `True`, draw items defined in this ogr_layer.
          count (int): The number of features in the layer record.
          exts (list): The exents of the layer's coverage.
          id (int): The unique identifier used by the drawing engine to identify the layer.
          geomColors (list or None): Optional list of Simple colors providing
            individual colors for each bit of geometry.
          selectedGeom (set): Indices of geometry marked as _selected_.
          volatile (bool): Whether or not the geometry is expected to change.

    Args:
        id (int): The id to assign the layer.
        vao (int): Vertex array object provided by the OpenGL API.
        buff (int): Array buffer provided by the OpenGL API.
        count (int): The number of features in the layer.
        exts (list): The extents of the enclosed geometry.
        volatile (bool): Whether or not the geometry is expected to change.
    """
    def __init__(self, id,vao=0, buff=0,count=0,exts=None,volatile=False,**kwargs):

        self.vao = vao
        self.buff = buff
        self.draw = True
        self.count = count
        self.exts = exts
        self.id = id
        self.labelLayer=-1
        self.parentLayer=-1
        if 'parent_layer' in kwargs:
            pLyr = kwargs['parent_layer']
            self.parentLayer = pLyr.id
            pLyr.labelLayer=self.id
        self.geomColors = []
        self.selectedRecs = np.full([self.count], 0, dtype=np.uint32)
        self.volatile=volatile

    def value_eq(self,other):
        """Compare another Layer Record to see if they are equivalentg.

        Args:
            other (LayerRecord): The other record to compare.

        Returns:
            bool: `True` if all values are equivalent; `False` otherwise.
        """

        return all((self.vao == other.vao,
                    self.buff == other.buff,
                    self.draw == other.draw,
                    self.count == other.count,
                    (len(self.exts)==0 and len(other.exts)==0) or self.exts == other.exts,
                    self.id == other.id,
                    (len(self.geomColors)==0 and len(other.geomColors)==0) or self.geomColors == other.geomColors,
                    (len(self.selectedRecs)==0 and len(other.selectedRecs)==0) or all(self.selectedRecs == other.selectedRecs),
                    self.volatile == other.volatile))
        
    def setSingleColor(self, c):
        """ Set a color for all components in a layer

        Args:
            c (glm.vec4): The color to assign.

        """
        pass

    def ClearBuffers(self):
        """ Delete associated OpenGL VAO and FBO.
        """
        if bool(glDeleteBuffers) and any([self.buff,self.vao]):
            glDeleteBuffers(1, [self.buff])
            glDeleteVertexArrays(1, [self.vao])

    def selectRecs(self,active):
        """ Mark specific records as 'selected'.

        Args:
            active (list): List of record indices to enable.
        """

        for a in active:
            self.selectedRecs[a] = 1

    def deselectRecs(self,inactive):
        """ Mark specific records as 'deselected'.

        Args:
            inactive (list): List of record indices to disable.
        """

        for i in inactive:
            self.selectedRecs[i] = 0

    def prepareForGLLoad(self,verts,ext,extra=None):
        """Perform any necessary preparation work prior to loading data into OpenGL.

        Args:
            verts (np.ndarray): Floats repreensting vertices.
            ext (list): Floats of data extents.
            extra (object,optional): Any additional data needed. Argument reserved for subclass implementations.

        Returns:
            tuple:
              0. np.ndarray: The vertices to use; default implementation returns `verts`, but subclass implementations
                             may return an alternative set.
              1. object: Default implementation returns `extra`, but subclass implementations may return a replacement
                         value.
        """
        self.buff = glGenBuffers(1)
        return verts,extra

    def loadGLBuffer(self,verts,drawMode,scene,extra=None):
        """Load some data into the currently bound VBO.

        Args:
            verts (numpy.ndarray): Vertex data to load into the array buffer.
            drawMode (int): The draw mode to attach to the buffer. Should be one of GL_STREAM_DRAW, GL_STREAM_READ,
                            GL_STREAM_COPY, GL_STATIC_DRAW, GL_STATIC_READ, GL_STATIC_COPY, GL_DYNAMIC_DRAW,
                            GL_DYNAMIC_READ, or GL_DYNAMIC_COPY.
            scene (GeometryGLScene): The scene tied to the active OpenGL context.
            extra (object,optional): Any additional data needed. Argument reserved for subclass implementations.
        """

        glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, drawMode)

    @property
    def vertCount(self):
        """int: Number of vertices associated with this record."""
        return self.count

class PolyLayerRecord(LayerRecord):
    """Polygon-specialized ogr_layer.

    Attributes:
        groups (list): list of (index,count) pairs that provide the offset and
           number of vertices in the vertex list that make up each polygon.
        refTex (int): Pointer for referenceTexture.
        customGradTexes(list): Pointer to value and gradient texture need for value
           coloring.
        refVao (int): Pointer to reference VAO.
        refBuff (int): Pointer to reference FBO.
        drawGrid (bool): Show/hide polygon outlines.
        fillGrid (bool): If `True` fill polygons.
        useFillAttrVals (bool): Fill with values intead of colors (DEPRECATED).
        gridColor (glm.vec4): Color to use to draw grid.
        attrVals (list): The values to associate with records.

    Args:
        id (int): The id to assign the layer.
        vao (int): Vertex array object provided by the OpenGL API.
        buff (int): Array buffer provided by the OpenGL API.
        polygroups (list): list of (index,count) pairs that provide the offset and
           number of vertices in the vertex list that make up each polygon.
    """
    def __init__(self, id, vao=0, buff=0, polygroups=(),hasAdjacency=False,**kwargs):
        super().__init__(id,vao, buff,len(polygroups), **kwargs)

        self.groups = polygroups
        self.refTex = 0
        self.customGradTexes = [0,0]
        self.refVao = 0
        self.refBuff = 0
        self.drawGrid = True
        self.fillGrid = kwargs.get('fill_grid',True)
        self.useFillAttrVals = False # DEPRECATED
        self.line_thickness = kwargs.get('line_thickness', 1)
        self.gridColor = glm.vec4(kwargs.get('grid_color',glm.vec4(0.,0.,0.,1.)))
        self.geomColors = [glm.vec4(1., 0., 0., 1.) for _ in range(len(polygroups))]
        self.attrVals = None
        self.fillMode = POLY_FILL.SOLID
        self.needsAdjacency = not hasAdjacency

        if 'single_color' in kwargs:
            self.setSingleColor(kwargs['single_color'])

    def value_eq(self,other):
        return all((super().value_eq(other),
                self.groups ==other.groups,
                self.refTex ==other.refTex,
                self.customGradTexes ==other.customGradTexes,
                self.refVao ==other.refVao,
                self.refBuff ==other.refBuff,
                self.drawGrid ==other.drawGrid,
                self.fillGrid ==other.fillGrid,
                self.useFillAttrVals ==other.useFillAttrVals,
                self.line_thickness ==other.line_thickness,
                self.gridColor ==other.gridColor,
                self.geomColors ==other.geomColors,
                self.attrVals ==other.attrVals))


    def setSingleColor(self, c):

        vC = glm.vec4(c)
        for i in range(len(self.geomColors)):
            self.geomColors[i] = vC

    def ClearBuffers(self):
        super().ClearBuffers()
        if bool(glDeleteBuffers) and any([self.refVao,self.refBuff]):
            glDeleteVertexArrays(1, [self.refVao])
            glDeleteBuffers(1,[self.refBuff])
            texes = [self.refTex]+self.customGradTexes
            glDeleteTextures(2,texes)

    def prepareForGLLoad(self,verts,ext,extra=None):
        
        self.buff = glGenBuffers(1)
        
        if not self.needsAdjacency:
            return verts,extra
       
        rCount = self.ringCount

        # make new buffer for verts
        newVerts=np.empty(len(verts)+(rCount*4),dtype=np.float32)
        i=0
        for grp in self.groups:
            for g in range(len(grp)):
                start, count = grp[g]
                newCount = count+2
                newStart = i//2

                # expand start and count to be componentwise instead of vertex wise
                start*=2
                count*=2
                end = start+count
                newVerts[i:i+2]= verts[end-4:end-2]
                i+=2
                newVerts[i:i+count]=verts[start:start+count]
                i+=count
                newVerts[i:i + 2] = verts[start+2:start+4]
                i+=2
                grp[g] = newStart,newCount

        self.needsAdjacency = False
        return newVerts,extra

    def loadGLBuffer(self, verts, drawMode,scene, extra=None):
        if extra is None:
            glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, drawMode)
        else:

            try:
                glEnableVertexAttribArray(1)
                # https://stackoverflow.com/questions/11132716/how-to-specify-buffer-offset-with-pyopengl
                glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(verts.nbytes))
                # allocate the space, then copy data, one array at a time
                glBufferData(GL_ARRAY_BUFFER, verts.nbytes + extra.nbytes, None, drawMode)
                glBufferSubData(GL_ARRAY_BUFFER, 0, verts.nbytes, verts)
                glBufferSubData(GL_ARRAY_BUFFER, verts.nbytes, extra.nbytes, extra)
            except OSError:
                print("Memory corruption with Visualizer. Please try restarting Program", file=sys.stderr)
                raise

    @property
    def vertCount(self):
        tot = 0
        for sublist in self.groups:
            for _,count in sublist:
                tot+=count
        return tot

    @property
    def ringCount(self):
        """int: The total number of polygon rings contained within the record."""
        tot = 0
        for sublist in self.groups:
            tot+=len(sublist)
        return tot

    @property
    def grid_thickness(self):
        """float: DEPRECATED"""
        # the grid_thickness property is DEPRECATED; use self.line_thickness instead
        return self.line_thickness

    @grid_thickness.setter
    def grid_thickness(self, value):
        # the grid_thickness property is DEPRECATED; use self.line_thickness instead
        self.line_thickness = value


class PointLayerRecord(LayerRecord):
    """ Point-specialized ogr_layer data.

    Attributes:
        ptSelBuff (int): Array buffer for selected points provided by
            the OpenGL API.
        count (int): Total number of points in this ogr_layer.

    Args:
        vao (int): Vertex array object provided by the OpenGL API.
        buff (int): Array buffer provided by the OpenGL API.
        count (int): Total number of points in this ogr_layer.
    """



    def __init__(self, id,vao=0, buff=0,count=0, **kwargs):
        super().__init__(id,vao, buff,count, **kwargs)
        self.ptSelBuff = 0
        self.auxColorBuff =0
        self._ptSize = kwargs.get('size',2.)
        self.colorMode=POINT_FILL.SINGLE

        # begin refvalue stuff
        self.scaleByValue = False # has effect only if colorbyvalue is active
        self.scaleMinSize = 1.
        self.scaleMaxSize = 1.
        self.clampColorToRange = False
        self.gradient = None
        self.valueBounds = [0.,1.]
        self.gradTexId = 0

        self.indexedGlyphs=kwargs.get('indexed_glyphs',[])
        self.indexedScales=kwargs.get('indexed_scales',[])

        # end refvalue stuff
        self._glyphCode = kwargs.get('glyph_code','.')
        if 'group_colors' in kwargs:
            self.geomColors = kwargs['group_colors']
            self.colorMode = POINT_FILL.GROUP
        elif 'single_color' in kwargs:
            self.geomColors =[ColorRange(kwargs['single_color'],0,count)]
        elif 'indexed_colors' in kwargs:
            self.colorMode = POINT_FILL.INDEX
            self.geomColors = kwargs['indexed_colors']
        elif 'value_gradient' in kwargs:
            self.colorMode = POINT_FILL.VAL_REF
            self.colorByValue=True
            self.gradient = kwargs['value_gradient']
            self.scaleByValue = kwargs.get('scale_by_value',False)
            self.scaleMinSize = kwargs.get('scale_min_size',1.)
            self.scaleMaxSize = kwargs.get('scale_max_size',1.)
            self.clampColorToRange = kwargs.get('clamp_colors',False)
            self.lowVal,self.highVal = kwargs.get('value_filter_range',[0,1])
        else:
            self.geomColors= [ColorRange(glm.vec4(1., 0., 0., 1.), 0, count)]


    def value_eq(self,other):

        return all((super().value_eq(other),
                    self.ptSelBuff == other.ptSelBuff,
                    self.auxColorBuff == other.auxColorBuff,
                    self.ptSize == other.ptSize,
                    self.colorMode == other.colorMode,
                    self.colorByValue == other.colorByValue,
                    self.scaleByValue == other.scaleByValue,
                    self.scaleMinSize == other.scaleMinSize,
                    self.scaleMaxSize == other.scaleMaxSize,
                    self.clampColorToRange == other.clampColorToRange,
                    self.lowVal==other.lowVal,
                    self.highVal==other.highVal,
                    self.glyphCode==other.glyphCode,
                    self.gradTexId == other.gradTexId,
                   (len(self.indexedScales)==0 and len(other.indexedScales)==0) or all(
                       [i==o for i,o in zip(self.indexedScales, other.indexedScales)]),
                    (len(self.indexedGlyphs) == 0 and len(other.indexedGlyphs) == 0) or all(
                       [i == o for i, o in zip(self.indexedGlyphs, other.indexedGlyphs)])

                    ))

    def setSingleColor(self, c):
        self.geomColors = [ColorRange(c,0,self.count)]
        self.colorMode = POINT_FILL.SINGLE
        # if bool(glVertexAttrib4f):
        #     glVertexAttrib4f(2, *self.geomColors[0].color)

    def ClearBuffers(self):
        if bool(glDeleteBuffers) and any([self.ptSelBuff, self.auxColorBuff]):

            glDeleteBuffers(2, [self.ptSelBuff, self.auxColorBuff])
            glDeleteTextures(1,[self.gradTexId])

        super().ClearBuffers()

    def prepareForGLLoad(self, verts, ext, extra=None):
        """For initializing the vertices and any other info for OpenGL loading"""

        self.buff, self.ptSelBuff = glGenBuffers(2)
        if self.colorMode in [POINT_FILL.INDEX, POINT_FILL.VAL_REF]:
            self.auxColorBuff = glGenBuffers(1)
        # default is passthru
        return verts,extra
    
    def loadGLBuffer(self,verts,drawMode,scene,extra=None):
        glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, drawMode)

        sBuff = extra if extra is not None else np.zeros(len(verts.ravel()) // 2, dtype=np.uint32)
        glBindBuffer(GL_ARRAY_BUFFER, self.ptSelBuff)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 1, GL_UNSIGNED_INT, GL_FALSE, 0, None)
        glBufferData(GL_ARRAY_BUFFER, sBuff.nbytes, sBuff, drawMode)

        # default attribute values
        # glVertexAttrib4f(2,*self.geomColors[0].color)
        # glVertexAttrib1f(3,self._ptSize)
        # glVertexAttribI1ui(4,ord(self.glyphCode))

        if self.colorMode == POINT_FILL.INDEX:
            expColors = IndexedColor.expandIndexes(self.geomColors, self.count)
            glBindBuffer(GL_ARRAY_BUFFER, self.auxColorBuff)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, 0, None)
            totBytes=expColors.nbytes

            expGlyphs=None
            expScales = None

            if len(self.indexedScales)>0:
                expScales=IndexedScale.expandIndexes(self.indexedScales,self.count)
                totBytes+=expScales.nbytes
                self._ptSize=None
            if len(self.indexedGlyphs)>0:
                expGlyphs=IndexedGlyph.expandIndexes(self.indexedGlyphs,self.count)
                totBytes+=expGlyphs.nbytes
                self._glyphCode = None

            glBufferData(GL_ARRAY_BUFFER, totBytes, None,GL_DYNAMIC_DRAW)
            glBufferSubData(GL_ARRAY_BUFFER,0,expColors.nbytes,expColors)
            offs=expColors.nbytes
            if expScales is not None:
                glEnableVertexAttribArray(3)
                glVertexAttribPointer(3,1,GL_FLOAT,GL_FALSE,0,ctypes.c_void_p(offs))
                glBufferSubData(GL_ARRAY_BUFFER,offs,expScales.nbytes,expScales)
                offs+=expScales.nbytes
            if expGlyphs is not None:
                glEnableVertexAttribArray(4)
                glVertexAttribIPointer(4, 1, GL_UNSIGNED_INT, 0, ctypes.c_void_p(offs))
                glBufferSubData(GL_ARRAY_BUFFER,offs,expGlyphs.nbytes,expGlyphs)

        elif self.colorMode == POINT_FILL.VAL_REF:
            glBindBuffer(GL_ARRAY_BUFFER, self.auxColorBuff)
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 0, None)
            glBufferData(GL_ARRAY_BUFFER, extra.nbytes, extra, drawMode)
            scene.SetGradientTexture(self.id, self.gradient)

    @property
    def ptSize(self):
        """float: size of point to draw, in pixels."""
        return self._ptSize

    @ptSize.setter
    def ptSize(self, value):
        if value!=self._ptSize:
            self._ptSize=value
            if bool(glVertexAttrib1f):
                glVertexAttrib1f(3, self._ptSize)

    @property
    def glyphCode(self):
        """int: The ord code for the glyph used to draw points."""
        return self._glyphCode

    @glyphCode.setter
    def glyphCode(self, value):
        if value!=self._glyphCode:
            self._glyphCode=value
            if bool(glVertexAttribI1ui):
                glVertexAttribI1ui(4, ord(self._glyphCode))


class LineLayerRecord(LayerRecord):
    """Record representing line geometry to be drawn.

    Attributes:

    Args:
        id (int): The id to assign the layer.
        vao (int,optional): Vertex array object provided by the OpenGL API.
        buff (int,optional): Array buffer provided by the OpenGL API.
        linegroups (list,optional): List of (start,count) tuples representing linestrings; can be `None` only if
                                    `segmentCount` is not `None`.
        segmentcount (int,optional): Total number of line segments; can be `None` only if `linegroups` is not `None`.

    Keyword Args:
        hasAdjacency (bool,optional): If `True` the adjacency geometry adjustments are skipped when `prepareGLLoad()` is
                                      called. Otherwise, adjacency geometry will be computed.
        lineThickness (float): How think each line should be drawn, in pixels.
        singleColor (glm.vec4): Color to render all lines in.
    """

    def __init__(self, id, vao=0, buff=0, linegroups=None,segmentcount=None,**kwargs):
        assert (linegroups is None and segmentcount is not None) or (linegroups is not None and segmentcount is None)

        self.needsAdjacency = True
        self.groups = None
        if linegroups is not None:
            count = len(linegroups)
            self.needsAdjacency = not kwargs.get('hasAdjacency',False)
            self.groups = linegroups
        else:
            count = segmentcount
        super().__init__(id,vao, buff,count, **kwargs)

        self.gradTexId = 0
        self.refVao = 0
        self.refBuff = 0
        self.drawGrid = True
        self.line_thickness = kwargs.get('line_thickness', 1)
        self.colorMode = LINE_FILL.SINGLE
        self.geomColors=[glm.vec4(0.,0.,0.,1.)]
        if 'single_color' in kwargs:
            self.geomColors[0]=kwargs['single_color']
        self.attrVals = None
        self.lowVal = 0.
        self.highVal = 1.

    def value_eq(self,other):
        return all((super().value_eq(other),
                self.groups ==other.groups,
                self.gradTexId ==other.gradTexId,
                self.refVao ==other.refVao,
                self.refBuff ==other.refBuff,
                self.drawGrid ==other.drawGrid,
                self.line_thickness ==other.line_thickness,
                self.geomColors ==other.geomColors,
                self.lowVal == other.lowVal,
                self.highVal == other.highVal,
                self.attrVals ==other.attrVals))


    def setSingleColor(self, c):
        vC = glm.vec4(c)
        for i in range(len(self.geomColors)):
            self.geomColors[i] = vC

    def ClearBuffers(self):
        super().ClearBuffers()
        if bool(glDeleteBuffers) and any([self.refVao,self.refBuff]):
            glDeleteVertexArrays(1, [self.refVao])
            glDeleteBuffers(1,[self.refBuff])
            texes = [self.gradTexId]
            glDeleteTextures(1,texes)

    def prepareForGLLoad(self,verts,ext,extra=None):
        self.buff = glGenBuffers(1)
        if extra is not None:
            self.refBuff = glGenBuffers(1)

        if not self.needsAdjacency:
            if self.groups is None:
                self.groups=[[s,4] for s in range(0,len(verts)//2,4)]
            return verts,extra

        newExtra=extra
        if self.groups is None:
            newVerts = np.empty(len(verts)*2,dtype=np.float32)

            self.groups = [[0,4] for _ in range(self.count)]
            insert=0

            for i in range(0,len(verts),4):
                self.groups[i//4][0]=insert//2

                newVerts[insert:insert+2]= verts[i:i + 2]
                insert+=2
                newVerts[insert:insert+4]=verts[i:i+4]
                insert+=4
                newVerts[insert:insert+2]= verts[i + 2:i + 4]
                insert+=2

            if extra is not None:
                newExtra = np.empty(len(extra) * 2, dtype=np.float32)
                for i in range(0, len(newExtra), 2):
                    nInd= i * 2
                    newExtra[nInd] = extra[i]
                    newExtra[nInd+1] = extra[i]
                    newExtra[nInd+2] = extra[i+1]
                    newExtra[nInd+3] = extra[i+1]
        else:
            i=0
            newVerts = np.empty(len(verts) + (len(self.groups) * 4), dtype=np.float32)
            for g in range(len(self.groups)):
                start,count= self.groups[g]
                newCount = count + 2
                newStart = i // 2

                # expand start and count to be componentwise instead of vertex wise
                start *= 2
                count *= 2
                end = start + count

                newVerts[i:i + 2] = verts[start:start+2]
                i += 2
                newVerts[i:i + count] = verts[start:start + count]
                i += count
                newVerts[i:i + 2] = verts[end-2:end]
                i += 2
                self.groups[g] = newStart, newCount

            if extra is not None:
                newExtra = np.empty(len(newVerts)//2, dtype=np.float32)
                i=0
                for g in range(len(self.groups)):
                    # group indicies are already transformed
                    start, count = self.groups[g]
                    end = start+count
                    newExtra[start]=extra[i]
                    newExtra[start+1:end-1]=extra[i:i+count-2]
                    newExtra[end-1] = extra[i+count-3]
                    i+=count-2


        self.needsAdjacency = False

        return newVerts,newExtra

    def loadGLBuffer(self,verts,drawMode,scene,extra=None):
        glBindBuffer(GL_ARRAY_BUFFER,self.buff)
        if extra is None:
            glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, drawMode)
        else:
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1,1,GL_FLOAT,GL_FALSE,0,ctypes.c_void_p(verts.nbytes))
            glBufferData(GL_ARRAY_BUFFER, verts.nbytes+extra.nbytes, None, drawMode)
            glBufferSubData(GL_ARRAY_BUFFER,0,verts.nbytes,verts)
            glBufferSubData(GL_ARRAY_BUFFER,verts.nbytes,extra.nbytes,extra)


    @property
    def vertCount(self):

        if self.groups is None:
            return self.count * 2
        tot = 0
        for _,count in self.groups:
            tot+=count
        return tot


class RasterLayerRecord(LayerRecord):
    """ Raster-specialized ogr_layer data.

    Attributes:
        texId (int): Texture id for raster image.
        smooth (bool): whether or not to apply smoothing to the texture.

    Args:
        vao (int): Vertex array object provided by the OpenGL API.
        buff (int): Array buffer provided by the OpenGL API.
        texId (int): Texture id for raster image provided by OpenGL API.
        gradTexId (int): optional id of 1D texture for gradient coloring provided by OpenGL API.

    """

    def __init__(self,id,vao=0, buff=0,texId=0, **kwargs):
        super().__init__(id,vao,buff, **kwargs)
        self.texId = texId
        self.smooth = kwargs.get('smooth',False)

    def ClearBuffers(self):
        super().ClearBuffers()
        if bool(glDeleteTextures) and self.texId!=0:
            glDeleteTextures(1,[self.texId])

    def prepareForGLLoad(self,verts,ext,extra=None):
        self.buff = glGenBuffers(1)
        self.texId = glGenTextures(1)
        
        return self._extToVerts(ext),extra

    def loadGLBuffer(self,verts,drawMode,scene,extra=None):
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(verts.nbytes))
        # allocate the space, then copy data, one array at a time
        glBufferData(GL_ARRAY_BUFFER, verts.nbytes + extra.nbytes, None, drawMode)
        glBufferSubData(GL_ARRAY_BUFFER, 0, verts.nbytes, verts)
        glBufferSubData(GL_ARRAY_BUFFER, verts.nbytes, extra.nbytes, extra)
        
    def _extToVerts(self,ext):
        self.count = 4
        left, right, bottom, top = ext
        return np.array([left, top,
                          left, bottom,
                          right, bottom,
                          right, top], dtype=np.float32)
        
class RasterIndexLayerRecord(RasterLayerRecord):
    """ Raster-specialized ogr_layer data.

    Attributes:
        texId (int): Texture id for raster image.
        gradTexId (int): optional id of 1D texture for gradient coloring.

    Args:
        vao (int): Vertex array object provided by the OpenGL API.
        buff (int): Array buffer provided by the OpenGL API.
        texId (int): Texture id for raster image provided by OpenGL API.
        gradTexId (int): optional id of 1D texture for gradient coloring provided by OpenGL API.

    """

    def __init__(self,id,vao=0, buff=0,texId=0,gradTexId=0, **kwargs):
        super().__init__(id,vao,buff,texId, **kwargs)
        self.gradTexId = gradTexId
        self.lowVal = 0.
        self.highVal = 1.
        self.clampColorToRange=False

    def ClearBuffers(self):
        super().ClearBuffers()
        if bool(glDeleteTextures) and self.gradTexId!=0:
            glDeleteTextures(1,[self.gradTexId])

    def prepareForGLLoad(self, verts, ext, extra=None):
        self.buff = glGenBuffers(1)
        self.texId, self.gradTexId = glGenTextures(2)

        return self._extToVerts(ext),extra

class ReferenceRecord(LayerRecord):
    """Reference to another layer record within the GaiaGeometryScene object. This exists reduce duplicate data
    sent to the GPU. ReferenceRecords operate in two ways: the default mode allows for overwriting of characteristics from
    the source layer; the alias can contain custom color, sizes, etc, while just sharing geometry. "Pure Alias" records
    act as read-only references to the src layer.

    Notes:
        * Attempting to access a ReferenceRecord whose source layer has been deleted is undefined.
        * All attributes from the source layer should be available through the ReferenceRecord instance; the attributes
        listed here are specific to ReferenceRecords

    Attributes:
        srcRecord (LayerRecord): The record to be referenced.

    Args:
        id (int): Unique identifier to assign to RefereneRecord.
        srcRecord (LayerRecord): The source LayerRecord object being referenced.
        pureAlias (bool,optional): If true, act as a read-only alias for source; otherwise, allows for local
          customization

    """

    def __init__(self,id,srcRecord,pureAlias=False):
        self.__dict__['_pureAlias']=False
        if isinstance(srcRecord,LayerRecord):
            super().__init__(id,srcRecord.vao,srcRecord.buff,srcRecord.count,srcRecord.exts)
        else:
            # id proxy
            super().__init__(id,0,0,0,[0,0,0,0])
        
        # remove any parent attributes that should be passthrough
        delattr(self,'vao')
        delattr(self,'buff')
        delattr(self,'draw')
        delattr(self,'count')
        delattr(self,'exts')
        delattr(self,'volatile')
        
        self.srcRecord = srcRecord

        if isinstance(srcRecord, LayerRecord):
            if not pureAlias:
                # copy for local use
                self.geomColors = self.srcRecord.geomColors[:]
            else:
                # direct reference
                self.geomColors = self.srcRecord.geomColors
        else:
            # id  proxy
            self.geomColors = []
        self._pureAlias = pureAlias

    def __getattr__(self, item):
        # cache fields here, as long as they are not in exclude tuple
        excludes=('groups',)#'exts')
        attr= getattr(self.srcRecord,item)
        if not self._pureAlias and item not in excludes:
            setattr(self,item,attr)
        return attr

    def __setattr__(self, key, value):

        # forbid assignment if pure alias
        if self._pureAlias:
            raise AttributeError('ReferenceRecord {} is set to "pureAlias"; values are read-only'.format(id))
        self.__dict__[key]=value

    def ClearBuffers(self):
        # do nothing; this is a weak reference to data managed elsewhere
        pass
    
    def prepareForGLLoad(self,verts,ext,extra=None):
        # dummy plug
        raise("Unimplemented; do not call")

    def loadGLBuffer(self,verts,drawMode,scene,extra=None):
        # dummy plug
        raise ("Unimplemented; do not call")

class TextLayerRecord(LayerRecord):
    """ Raster-specialized ogr_layer data.

    Attributes:
        texId (int): Texture id for raster image.
        smooth (bool): whether or not to apply smoothing to the texture.

    Args:
        vao (int): Vertex array object provided by the OpenGL API.
        buff (int): Array buffer provided by the OpenGL API.
        texId (int): Texture id for raster image provided by OpenGL API.
        gradTexId (int): optional id of 1D texture for gradient coloring provided by OpenGL API.

    """

    def __init__(self, id, vao=0, buff=0,txtRenderer=None,**kwargs):
        super().__init__(id, vao, buff, **kwargs)
        # self.texId = texId
        self._strEntries=[]
        self.scale_x = kwargs.get('x_scale',1.)
        self.scale_y = kwargs.get('y_scale',1.)
        self.outlineColor = kwargs.get("outline_color",None)
        self._vCount=0
        self.txtRenderer=txtRenderer

    def ClearBuffers(self):
        super().ClearBuffers()


    def AddStringEntry(self,strEntry):
        """Add a new string to the layer.

        Args:
            strEntry (StringEntry): The entry object containing the string and its location.
        """
        self._strEntries.append(strEntry)

    def AddString(self,inStr,anchor,**kwargs):
        """Add a new string to the layer.

        Args:
            inStr: The string to store; note that tabs will be converted to spaces.
            anchor: The point which "anchors" the string in Worldspace coordinates. The value should be a container with
                3 float values, corresponding to (x,y).

        Keyword Args:
            h_justify: String representing the horizontal justification relative to the anchor point. Valid values are:
                  * 'center': The string centers horizontally on the anchor point. This is the default value.
                  * 'left': The string positions itself so the anchor is to the left.
                  * 'right': The string positions itself so the anchor is to the right.
            v_justify: String representing the vertical justification relative to the anchor point. Valid values are:
                  * 'center': The string centers vertically on the anchor point. This is the default value.
                  * 'top': The string positions itself so the anchor is on top.
                  * 'bottom': The string positions itself so the anchor is below the bottom.
            tabspacing: The number of spaces to substitute for tab characters. The default is 4.


        """
        self._strEntries.append(StringEntry(inStr,anchor,**kwargs))

    def AddStrings(self,inStrs,anchors,**kwargs):
        """Add several strings to the layer

        Args:
            inStrs (list): A list of strings to add.
            anchors (numpy.ndarray): A list of floats corresponding to the anchor points for each string.

        Keyword Args:
            h_justify: String representing the horizontal justification relative to the anchor point. Valid values are:
                  * 'center': The string centers horizontally on the anchor point. This is the default value.
                  * 'left': The string positions itself so the anchor is to the left.
                  * 'right': The string positions itself so the anchor is to the right.
            v_justify: String representing the vertical justification relative to the anchor point. Valid values are:
                  * 'center': The string centers vertically on the anchor point. This is the default value.
                  * 'top': The string positions itself so the anchor is on top.
                  * 'bottom': The string positions itself so the anchor is below the bottom.
            tabspacing: The number of spaces to substitute for tab characters. The default is 4.

        """
        for s,a in zip(inStrs,anchors):
            self.AddString(s,a,**kwargs)

    def prepareForGLLoad(self, verts, ext, extra=None):
        # dummy plug
        raise ("Unimplemented; do not call")

    def loadGLBuffer(self, verts, drawMode, scene, extra=None):
        # dummy plug
        raise ("Unimplemented; do not call")

    def loadStrings(self):
        """Load strings into VAO and VBO associated with the record."""
        self._vCount = self.txtRenderer.loadStrings(self.vao,self.buff,self._strEntries,self.scale_x,self.scale_y)

    @property
    def vertCount(self):
        return self._vCount

    @property
    def strEntries(self):
        """list: List of StringEntry objects describing the strings present in the layer."""
        return self._strEntries
# </editor-fold>

