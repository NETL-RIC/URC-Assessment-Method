"""Scene compatible with gdal/ogr data."""
from __future__ import print_function, division, absolute_import, unicode_literals

import numpy as np
from OpenGL.GL import *
from osgeo import ogr, osr, gdal

from .geometryglscene import GeometryGLScene, GradientRecord


# from . import newStringEntry

# TODO: Change name to reflect more than just OGR support
# TODO: Ensure that both direct and transform values are supported.

class OGRGLScene(GeometryGLScene):
    """Subclass of GAIAGLScene that adds support for directly loading data from OGR.

    Args:
        widget (object,optional): The parent object that will manage the OpenGL context for the hosting UI framework.
        refreshkey (str,optional): Name of function to call from `widget` whenever the draw state changes.
        getextKey (str,optional): Name of function to call from `widget` whenever draw extents are needed.
    """



    def __init__(self, *args,**kwargs):

        super().__init__(*args,**kwargs)

        self._fids={}
        self._spatRefs = {}
        self._ogr_caches = {}


    def initializeGL(self):
        super().initializeGL()

        for k, v in self._ogr_caches.items():
            for args in v:
                getattr(self, k)(*args)
        self._ogr_caches.clear()


    def PolyLayerFromOgrLyr(self, lyr,**kwargs):
        """ Import Geometry from a previously loaded polygon ogr_layer.

        Args:
            lyr (ogr.Layer): Layer containing the geometry to import.

        Returns:
            int,int: The new ogr_layer id, and the total number of polygons imported.

        """

        # TODO: validate that the ogr_layer is of a polygon type

        fMap = {}

        ret = None
        if lyr is not None:
            sRef=lyr.GetSpatialRef()
            verts = []
            ptCount = 0
            polyCount = 0
            # pts = []
            polygroups = []
            polyExt=np.empty([4],dtype=np.float32)

            lbls = None
            lblArgs = None
            lblFldInd = -1
            if 'lbl_field' in kwargs:

                lblName = kwargs['lbl_field']
                lblFldInd = lyr.GetLayerDefn().GetFieldIndex(lblName)
                lblXInd=None
                lblYInd=None
                if lblFldInd != -1:
                    lbls = []
                    lblArgs = self._getLabellingArgs(kwargs)
                    if lblArgs['h_justify']=='right':
                        lbXInd=0
                    elif lblArgs['h_justify']=='left':
                        lblXInd=1
                    if lblArgs['v_justify']=='bottom':
                        lblYInd=2
                    elif lblArgs['v_justify']=='top':
                        lblYInd=3

            for feat in lyr:

                if feat is not None:
                    fId=feat.GetFID()

                    # geom = ogr.ForceToPolygon(feat.GetGeometryRef())
                    geom = feat.GetGeometryRef()
                    if geom.GetGeometryType() != ogr.wkbMultiPolygon:
                        # assume polygon
                        newGeom = ogr.Geometry(ogr.wkbMultiPolygon)
                        newGeom.AddGeometry(geom)
                        geom = newGeom
                    geom.CloseRings()
                    fMap[polyCount] = fId

                    rings = []
                    locCount = 0
                    for poly in geom:
                        for ring in poly:
                            locCount = 0
                            rCount = ring.GetPointCount()

                            # for adjacency
                            refInd = len(verts)
                            pt = ring.GetPoint(rCount-2)[0:2]
                            polyExt[0]=pt[0]
                            polyExt[1]=pt[0]
                            polyExt[2]=pt[1]
                            polyExt[3]=pt[1]
                            verts+=pt
                            locCount+=1


                            for j in range(rCount):
                                #pt = ring.GetPoint(j)[0:2]
                                # skip duplicate points (affects normal calculations
                                # if len(verts)>=2 and (pt[0]==verts[-2] or pt[1]==verts[-1]):
                                #     continue
                                pt = ring.GetPoint(j)[0:2]
                                polyExt[0]=min(polyExt[0],pt[0])
                                polyExt[1] = max(polyExt[0], pt[0])
                                polyExt[2] = min(polyExt[1], pt[1])
                                polyExt[3] = max(polyExt[1], pt[1])
                                # duplicate check
                                if np.float32(pt[0])!=np.float32(verts[-2]) or \
                                        np.float32(pt[1])!=np.float32(verts[-1]):
                                    verts +=pt
                                    locCount += 1

                            # special case: if all points overlap when converted to float 32
                            if len(verts)-refInd<=2:
                                # remove overlap point
                                verts[-2:]=[]
                                locCount-=1
                                continue
                            verts+=verts[refInd+4:refInd+6]
                            locCount+=1

                            rings.append((ptCount, locCount))
                            ptCount += locCount
                            assert ptCount==len(verts)//2

                    polygroups.append(rings)
                    polyCount+=1

                    if lblFldInd!=-1:
                        lbl=feat.GetFieldAsString(lblFldInd)
                        centroid = geom.Centroid()
                        anchor = [centroid.GetX(), centroid.GetY()]
                        if lblXInd is not None:
                            anchor[0] = polyExt[lblXInd]
                        if lblYInd is not None:
                            anchor[1] = polyExt[lblYInd]
                        lbls.append((lbl,anchor))

                else:
                    print("Missing fid: "+str(feat.GetFID()))
            lyr.ResetReading()

            verts = np.array(verts, dtype=np.float32)
            ext = lyr.GetExtent()


            ret = (self.AddPolyLayer(verts, polygroups, ext,hasAdjacency=True,**kwargs),len(polygroups))
            if lbls is not None:
                lblArgs['parent_layer']= self.GetLayer(ret[0])
                self.AddTextLayer(lbls,**lblArgs)

            self._fids[ret[0]]=fMap
            self._spatRefs[ret[0]] = sRef

        return ret

    def PointLayerFromOgrLyr(self, lyr,**kwargs):
        """ Import Geometry from a previously loaded point ogr_layer.

        Args:
            lyr (ogr.Layer): Layer containing the geometry to import.

        Returns:
            int,int: The new ogr_layer id, and the total number of points imported.
        """

        lbls=None
        lblArgs=None
        lblFldInd=-1
        if 'lbl_field' in kwargs:

            lblName=kwargs['lbl_field']
            lblFldInd=lyr.GetLayerDefn().GetFieldIndex(lblName)
            if lblFldInd!=-1:
                lbls = []
                lblArgs = self._getLabellingArgs(kwargs)
        # TODO: validate that lyr is points
        ret = None
        if lyr is not None:
            sRef=lyr.GetSpatialRef()

            ptCount = 0
            verts = []

            # ensure that the reading is set.
            lyr.ResetReading()
            for feat in lyr:
                geom = feat.GetGeometryRef()
                for j in range(geom.GetPointCount()):
                    coord = geom.GetPoint(j)[0:2]
                    verts += coord
                    ptCount += 1

                    if lblFldInd!=-1:
                        lbl=feat.GetFieldAsString(lblFldInd)
                        lbls.append((lbl,coord))
            lyr.ResetReading()
            verts = np.array(verts, dtype=np.float32)
            ext = lyr.GetExtent()


            ret = (self.AddPointLayer(verts, ext, **kwargs), ptCount)
            if lbls is not None:
                lblArgs['parent_layer']= self.GetLayer(ret[0])
                self.AddTextLayer(lbls,**lblArgs)
            self._spatRefs[ret[0]] = sRef
        return ret

    def LineLayerFromOgrLyr(self,lyr,**kwargs):
        """ Import Geometry from a previously loaded line ogr_layer.

        Args:
            lyr (ogr.Layer): Layer containing the geometry to import.

        Returns:
            int,int: The new ogr_layer id, and the total number of points imported.
        """

        ret = None
        if lyr is not None:
            sRef = lyr.GetSpatialRef()

            groups = []
            ptCount = 0
            verts =[]
            fMap = {}

            # ensure that the reading is set.
            lyr.ResetReading()
            for lineCount,feat in enumerate(lyr):
                fid = feat.GetFID()
                fMap[lineCount] = fid
                gStart = ptCount
                geom = feat.GetGeometryRef()
                for j in range(geom.GetPointCount()):
                    verts += geom.GetPoint(j)[0:2]
                    ptCount += 1
                groups.append((gStart,ptCount-gStart))
            lyr.ResetReading()
            verts = np.array(verts, dtype=np.float32)
            ext = lyr.GetExtent()

            ret = (self.AddLineLayer(verts, ext, linegroups=groups,**kwargs), len(groups))
            self._fids[ret[0]] = fMap
            self._spatRefs[ret[0]] = sRef
        return ret

    def _getLabellingArgs(self,kwargs):
        """Separate out label specific keyword arguments from a general argument dict.

        Args:
            kwargs (dict): The keyword arguments to parse.

        Returns:
            dict: Keyword arguments suitable for passing to `self.AddTextLayer()`.
        """

        pos = kwargs.get('lbl_pos', 'center')
        h_just = 'center'
        if pos in ('topleft', 'left', 'bottomleft'):
            h_just = 'right'
        elif pos in ('topright', 'right', 'bottomright'):
            h_just = 'left'
        v_just = 'center'
        if pos in ('topleft', 'top', 'topright'):
            v_just = 'bottom'
        elif pos in ('bottomleft', 'bottom', 'bottomright'):
            v_just = 'top'
        lblArgs = {'h_justify': h_just,
                   'v_justify': v_just}
        if 'lbl_color' in kwargs:
            lblArgs['color'] = kwargs['lbl_color']
        if 'lbl_font' in kwargs:
            lblArgs['font_path'] = kwargs['lbl_font']
        if 'lbl_pt_size' in kwargs:
            lblArgs['font_pt']=kwargs['lbl_pt_size']
        return lblArgs

    @staticmethod
    def _readBand(h,w,band):
        return band.ReadAsArray(0, 0, w, h, buf_xsize=w, buf_ysize=h, buf_type=gdal.GDT_Float32)

    def RasterColorBand(self,h,w,ds):
        """Retrieve RGBA color bands for the image.

        Args:
            h (int): The height of the image, in pixels.
            w (int): The width of the image, in pixels.
            ds (osgeo.gdal.Dataset): The Dataset with the image data to retrieve.

        Returns:
            numpy.ndarray: The image data divided into RGBA channels; shape is (`h`,`w`,4).
        """

        # this is a bit of a hack;
        # Assumptions:
        #   * colors are stored in red, green, blue, alpha color bands
        #    - ok to be missing a few, but will miss if other bands are used
        #   * channels are 8bit ints
        r, g, b, a = None, None, None, None
        for i in range(1, ds.RasterCount + 1):
            band = ds.GetRasterBand(i)
            ch = band.GetColorInterpretation()
            if ch == gdal.GCI_RedBand:
                r = OGRGLScene._readBand(h,w,band)
            elif ch == gdal.GCI_GreenBand:
                g = OGRGLScene._readBand(h,w,band)
            elif ch == gdal.GCI_BlueBand:
                b = OGRGLScene._readBand(h,w,band)
            elif ch == gdal.GCI_AlphaBand:
                a = OGRGLScene._readBand(h,w,band)

        divisor = 255.  # byte
        if ds.GetRasterBand(1).DataType in (gdal.GDT_Float32, gdal.GDT_Int32, gdal.GDT_CInt32, gdal.GDT_UInt32):
            divisor = 1.
        if r is None:
            r = np.zeros((h, w), dtype=np.float32)
        if g is None:
            g = np.zeros((h, w), dtype=np.float32)
        if b is None:
            b = np.zeros((h, w), dtype=np.float32)
        if a is None:
            a = np.full((h, w), divisor, dtype=np.float32)

        img = np.dstack((r, g, b, a))
        img /= divisor

        return img

    def RasterGrayBand(self,h,w,ds):
        """Retrieve the grayscale band for the image.

        Args:
            h (int): The height of the image, in pixels.
            w (int): The width of the image, in pixels.
            ds (osgeo.gdal.Dataset): The Dataset with the image data to retrieve.

        Returns:
            numpy.ndarray: The image grayscale band; shape is (`h`,`w`).
        """
        band = ds.GetRasterBand(1)
        noData = band.GetNoDataValue()
        vals = OGRGLScene._readBand(h,w,band)
        # normalize
        vMax= -np.inf
        vMin=np.inf
        flat = vals.ravel()
        for v in flat:
            if v==noData:
                continue
            if v < vMin:
                vMin = v
            if v > vMax:
                vMax = v

        vRange = vMax-vMin
        for i in range(len(flat)):
            if flat[i]!=noData:
                flat[i] = (flat[i]-vMin)/vRange
            else:
                flat[i]=-1.
        # divisor = 255.  # byte
        # if band.DataType in (gdal.GDT_Float32, gdal.GDT_Int32, gdal.GDT_CInt32, gdal.GDT_UInt32):
        #     divisor = 1.
        # vals /= divisor
        return vals

    def _rasterLayerFromGdalLyr(self,ds):
        """Retrieve raster data from a GDAL dataset.

        Args:
            ds (osgeo.gdal.Dataset): The dataset to extract the raster from.

        Returns:
            tuple: numpy.ndarray the data composing the image, and a list of the geospatial extents.
        """

        minX, pX, _, maxY, _, pY = ds.GetGeoTransform()
        maxX = minX + ((ds.RasterXSize - 1) * pX)
        minY = maxY + ((ds.RasterYSize - 1) * pY)

        h = ds.RasterYSize
        w = ds.RasterXSize

        if ds.RasterCount == 1 and ds.GetRasterBand(1).GetColorInterpretation() in (gdal.GCI_GrayIndex,gdal.GCI_PaletteIndex,gdal.GCI_Undefined):
            img=self.RasterGrayBand(h,w,ds)
        else:
            img=self.RasterColorBand(h,w,ds)

        if minX>maxX:
            minX,maxX=maxX,minX
            img = np.flip(img, axis=1)
            # pX*=-1
        if minY>maxY:
            minY,maxY=maxY,minY
            img = np.flip(img, axis=0)
            # pY*=-1

        # if pX<0:
        #     #origin on right
        #     img=np.flip(img,axis=1)
        # if pY<0:
        #     # origin on bottom
        #     img=np.flip(img,axis=0)

        return img,[minX,maxX,minY,maxY]

    def RasterImageLayerFromGdalLyr(self, ds):
        """Create an image raster layer from a GDAL raster layer.

        Args:
            ds (osgeo.gdal.Dataset): the Dataset containing the raster to load.

        Returns:
            int: The id of the newly created layer.
        """

        img,exts = self._rasterLayerFromGdalLyr(ds)

        id=self.AddRasterImageLayer(img,GL_RGBA,exts)
        sRef = ds.GetSpatialRef()
        self._spatRefs[id] = sRef
        return id

    def RasterIndexLayerFromGdalLyr(self,ds,gradObj=GradientRecord()):
        """Create an indexed value raster layer from a GDAL raster layer.

        Args:
            ds (osgeo.gdal.Dataset): the Dataset containing the raster to load.
            gradObj (GradientRecord,optional): Custom gradient to assign, if any.

        Returns:
            int: The id of the newly created layer.
        """

        img,exts = self._rasterLayerFromGdalLyr(ds)
        id=self.AddRasterIndexedLayer(img,GL_RED,exts,GL_R32F,gradObj)
        sRef = ds.GetSpatialRef()
        self._spatRefs[id] = sRef
        return id

    def OpenPolyLayer(self,path,**kwargs):
        """ Import polygon data from a file using OGR to interpret.

        Args:
            path (str): Path to the file to load.

        Returns:
            int: The total number of polygons imported.
        """

        ds = ogr.Open(path)
        lyr = ds.GetLayer(0)
        return self.PolyLayerFromOgrLyr(lyr,**kwargs)


    def OpenPtLayer(self,path,**kwargs):
        """ Import point data from a file using OGR to interpret.

        Args:
            path (str): Path to the file to load.

        Returns:
            int: The total number of points imported.
        """

        ds = ogr.Open(path)
        lyr = ds.GetLayer(0)
        return self.PointLayerFromOgrLyr(lyr,**kwargs)

    def OpenLineLayer(self,path,**kwargs):
        """ Import line data from a file using OGR to interpret.

        Args:
            path (str): Path to the file to load.

        Returns:
            int: The total number of lines imported.
        """
        ds = ogr.Open(path)
        lyr = ds.GetLayer(0)
        return self.LineLayerFromOgrLyr(lyr,**kwargs)

    def OpenRasterImageLayer(self, path):
        """Load a raster image layer from a file supported by GDAL.

        Args:
            path (str): Path to the file to load.

        Returns:
            int: the id of the newly created layer.
        """

        ds = gdal.Open(path)
        return self.RasterImageLayerFromGdalLyr(ds)

    def OpenRasterIndexLayer(self,path,gradObj=GradientRecord()):
        """Load an index value raster layer from a file supported by GDAL.

        Args:
            path (str): Path to the file to load.
            gradObj (GradientRecord,optional): Custom gradient to assign, if any.

        Returns:
            int: the id of the newly created layer.
        """

        ds = gdal.Open(path)
        return self.RasterIndexLayerFromGdalLyr(ds,gradObj)

    def GetSelectedFIDs(self,lyrId):
        """Retrieve FIDs for any selected features in a layer.

        Args:
            lyrId (int): Id of layer to query.

        Returns:
            set: indices of any features that are selected within the layer.
        """

        rec = self._layers[lyrId]
        ret = set()
        for p in range(len(rec.selectedRecs)):
            if rec.selectedRecs[p]:
                ret.add(self._fids[rec.id][p])
        return ret

    def DeleteLayer(self, id):

        # add default argument to pop since we don't care if the key is absent
        self._fids.pop(id,None)
        self._spatRefs.pop(id,None)
        super().DeleteLayer(id)

    def ClearPolyLayers(self):
        idCache = tuple(self._polyLayerIds)
        for id in idCache:
            self._spatRefs.pop(id, None)
            self._fids.pop(id,None)
        super().ClearPolyLayers()

    def ClearPointLayers(self):
        idCache = tuple(self._pointLayerIds)
        for id in idCache:
            self._spatRefs.pop(id,None)
        super().ClearPointLayers()

    def ClearLineLayers(self):
        idCache = tuple(self._lineLayerIds)
        for id in idCache:
            self._spatRefs.pop(id,None)
            self._fids.pop(id, None)
        super().ClearLineLayers()

    def ClearAllLayers(self):
        self._fids.clear()
        self._spatRefs.clear()
        super().ClearAllLayers()

    def ReprojectLayer(self,id,toSRef):
        """Reproject a given layer to another SRS.

        Args:
            id (int): The layer to transform.
            toSRef (osgeo.osr.SpatialReference): The SRS to reproject into.
        """

        if self._initialized:
            fromSRef = self._spatRefs.get(id,None)

            if fromSRef is not None and fromSRef.IsSame(toSRef) == 0:
                transForm=osr.CoordinateTransformation(fromSRef,toSRef)
                rec=self.GetLayer(id)

                bytecount = rec.vertCount * 2 * np.dtype(np.float32).itemsize
                self._beginContext()
                glBindVertexArray(rec.vao)
                glBindBuffer(GL_ARRAY_BUFFER,rec.buff)
                verts=np.frombuffer(glGetBufferSubData(GL_ARRAY_BUFFER,0,bytecount),dtype=np.float32)

                verts=verts.reshape([rec.vertCount,2])
                verts=np.array(transForm.TransformPoints(verts),np.float32)[:,:2]

                rec.exts = [np.min(verts[:,0]),
                            np.max(verts[:,0]),
                            np.min(verts[:,1]),
                            np.max(verts[:,1])
                            ]

                glBufferSubData(GL_ARRAY_BUFFER,0,verts.nbytes,verts)
                glBindVertexArray(0)
                self.recalcMaxExtentsFromLayers()
                self._endContext()
        else:
            self._ogr_caches.setdefault('ReprojectLayer',[]).append((id,toSRef))


'''
        
        count = pxlData.shape[0]

        if count == 1 or len(pxlData.shape)<3:
            channels = GL_RED
        elif count==2:
            channels = GL_RG
        elif count==3:
            channels = GL_RGB
        elif count==4:
            channels = GL_RGBA
        else:
            raise GaiaGLException(f'Texture data cannot have {count} channels')'''
