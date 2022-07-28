from __future__ import print_function, division, absolute_import, unicode_literals

import numpy as np
from OpenGL.GL import *
from osgeo import ogr, osr, gdal

from .geometryglscene import GeometryGLScene, GradientRecord


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
                            verts+=ring.GetPoint(rCount-2)[0:2]
                            locCount+=1


                            for j in range(rCount):
                                #pt = ring.GetPoint(j)[0:2]
                                # skip duplicate points (affects normal calculations
                                # if len(verts)>=2 and (pt[0]==verts[-2] or pt[1]==verts[-1]):
                                #     continue
                                pt = ring.GetPoint(j)[0:2]
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
                else:
                    print("Missing fid: "+str(feat.GetFID()))
            lyr.ResetReading()

            verts = np.array(verts, dtype=np.float32)
            ext = lyr.GetExtent()


            ret = (self.AddPolyLayer(verts, polygroups, ext,hasAdjacency=True,**kwargs),len(polygroups))
            self._fids[ret[0]]=fMap
            self._spatRefs[ret[0]] = sRef

        return ret

    def PointLayerFromOgrLyr(self, lyr,**kwargs):
        """ Import Geometry from a previously loaded polygon ogr_layer.

        Args:
            lyr (ogr.Layer): Layer containing the geometry to import.

        Returns:
            int,int: The new ogr_layer id, and the total number of points imported.
        """

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
                    verts += geom.GetPoint(j)[0:2]
                    ptCount += 1
            lyr.ResetReading()
            verts = np.array(verts, dtype=np.float32)
            ext = lyr.GetExtent()


            ret = (self.AddPointLayer(verts, ext,**kwargs),ptCount)
            self._spatRefs[ret[0]] = sRef

        return ret

    def LineLayerFromOgrLyr(self,lyr,**kwargs):
        """

        Args:
            lyr:
            **kwargs:

        Returns:

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

    @staticmethod
    def _readBand(h,w,band):
        return band.ReadAsArray(0, 0, w, h, buf_xsize=w, buf_ysize=h, buf_type=gdal.GDT_Float32)

    def RasterColorBand(self,h,w,ds):
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


        minX, pX, _, maxY, _, pY = ds.GetGeoTransform()
        maxX = minX + ((ds.RasterXSize - 1) * pX)
        minY = maxY + ((ds.RasterYSize - 1) * pY)

        h = ds.RasterYSize
        w = ds.RasterXSize

        if ds.RasterCount == 1 and ds.GetRasterBand(1).GetColorInterpretation() in (gdal.GCI_GrayIndex,gdal.GCI_PaletteIndex,gdal.GCI_Undefined):
            img=self.RasterGrayBand(h,w,ds)
        else:
            img=self.RasterColorBand(h,w,ds)

        return img,[minX,maxX,minY,maxY]

    def RasterImageLayerFromGdalLyr(self, ds):

        img,exts = self._rasterLayerFromGdalLyr(ds)
        return (self.AddRasterImageLayer(img,GL_RGBA,exts))

    def RasterIndexLayerFromGdalLyr(self,ds,gradObj=GradientRecord()):

        img,exts = self._rasterLayerFromGdalLyr(ds)
        return self.AddRasterIndexedLayer(img,GL_RED,exts,GL_R32F,gradObj)

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
        """

        Args:
            path:

        Returns:

        """
        ds = ogr.Open(path)
        lyr = ds.GetLayer(0)
        return self.LineLayerFromOgrLyr(lyr,**kwargs)

    def OpenRasterImageLayer(self, path):

        ds = gdal.Open(path)
        return self.RasterImageLayerFromGdalLyr(ds)

    def OpenRasterIndexLayer(self,path,gradObj=GradientRecord()):
        ds = gdal.Open(path)
        return self.RasterIndexLayerFromGdalLyr(ds,gradObj)

    def GetSelectedFIDs(self,lyrId):


        rec = self._layers[lyrId]
        ret = set()
        for p in range(len(rec.selectedRecs)):
            if rec.selectedRecs[p]:
                ret.add(self._fids[rec.id][p])
        return ret

    # def _getRefID(self, stackId, polyId, recId):
    #     return self._fids[recId][polyId]

    def _getPolyGroupID(self,lyr,rId):
        for k,v in self._fids[lyr].items():
            if v == rId:
                return k
        raise KeyError("rId not found in record.")

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