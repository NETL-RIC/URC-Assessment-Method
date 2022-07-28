from abc import ABCMeta, abstractmethod
from inspect import isclass

import numpy as np

from ._support import *
from ._version import VERSION as GAIAVIZ_VERSION, check_version
from .geometryglscene import GaiaGLException


#=========================================
# Exceptions
# ----------------------------------------
class GaiaGLCacheException(GaiaGLException):
    pass

#=========================================
# Useful constants
# ----------------------------------------
PT_DT = np.dtype('<2f4')
C_DT = np.dtype('<u4')
V4_DT = np.dtype('<4f4')
GROUP_DT = np.dtype('<u4, <u4')

#=========================================
# Abstract base classes
# ----------------------------------------

class VizCache(object,metaclass=ABCMeta):


    def __init__(self,obj,*args,**kwargs):
        self._obj = obj if not isclass(obj) else obj(*args,**kwargs)

    @abstractmethod
    def readFromStream(self,strm):
        ...

    @abstractmethod
    def skipInStream(self,strm):
        ...

    @abstractmethod
    def writeToStream(self,strm):
        ...


    # @property
    # @abstractmethod
    # def writeSize(self):
    #     ...

    @property
    def obj(self):
        return self._obj

#=========================================
# Concrete classes
# ----------------------------------------
#    Colors

class GradientCache(VizCache):

    def __init__(self, obj=None, *args, **kwargs):
        if obj is None:
            obj=GradientRecord
        super().__init__(obj,*args,**kwargs)

    def readFromStream(self, strm):

        self._obj.clear()
        count = np.fromfile(strm,np.uint32,1)[0]
        gradBuff = np.fromfile(strm,np.float32,count*5)
        for buff in gradBuff.reshape([count,5]):
            wt=buff[0]
            self._obj[wt]=glm.vec4(buff[1:])


    def skipInStream(self,strm):
        count = np.fromfile(strm,np.uint32,1)[0]
        strm.seek(np.float32.itemsize*count*5,1)


    def writeToStream(self, strm):

        strm.write(np.array([len(self._obj)],dtype=np.uint32).tobytes())
        buff = np.empty([5],dtype=np.float32)
        for buff[0], buff[1:] in self._obj:
            strm.write(buff.tobytes())


    # @property
    # def writeSize(self):
    #     # 5 float32s per entry + entry count
    #     return (len(self._obj)*np.dtype(np.float32).itemsize * 5) + (np.dtype(np.uint32).itemsize)
    #



class ColorRangeCache(VizCache):

    _dt = np.dtype('<4f4, <2u4')

    def __init__(self, obj=None):
        if obj is None:
            obj = ColorRange
        super().__init__(obj,color=glm.vec4(),start=0,count=0)

    def readFromStream(self, strm):
        buff = np.fromfile(strm,ColorRangeCache._dt,1)
        self._obj.color,(self._obj.start,self._obj.count)=buff[0]
        self._obj.color=glm.vec4(self._obj.color)

    def skipInStream(self,strm):
        strm.seek(ColorRangeCache._dt.itemsize,1)

    def writeToStream(self, strm):

        strm.write(np.array([(self._obj.color,(self._obj.start,self._obj.count))],dtype=ColorRangeCache._dt).tobytes())

    # @property
    # def writeSize(self):
    #     return ColorRangeCache._dt.itemsize

class IndexedCache(VizCache,metaclass=ABCMeta):

    @abstractmethod
    def _typeCode(self):
        ...

    def _readBuff(self,strm):
        count = np.fromfile(strm, '<u4', 1)[0]
        dt = np.dtype(f'{self._typeCode()}, <{count}u4')
        buff =  np.fromfile(strm, dt, 1)

        self._obj.inds = list(buff[0][1])
        return buff[0][0]

    def _gen_dt(self,count=None):
        if count is None:
            count = len(self.obj)
        return np.dtype(f'<u4, {self._typeCode()}, <{count}u4')

    def skipInStream(self,strm):
        count = np.fromfile(strm, '<u4', 1)[0]
        dt = np.dtype(f'{self._typeCode()}, <{count}u4')
        strm.seek(dt.itemsize,1)

class IndexedColorCache(IndexedCache):

    def _typeCode(self):
        return '<4f4'

    def __init__(self, obj=None):
        if obj is None:
            obj = IndexedColor
        super().__init__(obj,color=glm.vec4(),inds=())

    def readFromStream(self, strm):
        color = self._readBuff(strm)
        self._obj.color= glm.vec4(color)

    def writeToStream(self, strm):
        dt = self._gen_dt()
        strm.write(np.array([(len(self._obj.inds),self._obj.color,self._obj.inds)],dtype=dt).tobytes())


    # @property
    # def writeSize(self):
    #     return self._gen_dt().itemsize

class IndexedGlyphCache(IndexedCache):

    def _typeCode(self):
        return '<u4'

    def __init__(self, obj=None):
        if obj is None:
            obj = IndexedGlyph
        super().__init__(obj, glyph='.',inds=())

    def readFromStream(self, strm):
        glyphVal = self._readBuff(strm)
        self._obj.glyphVal= glyphVal

    def writeToStream(self, strm):
        dt = self._gen_dt()
        strm.write(np.array([(len(self._obj.inds),self._obj.glyphVal,self._obj.inds)],dtype=dt).tobytes())


class IndexedScaleCache(IndexedCache):

    def _typeCode(self):
        return '<f4'

    def __init__(self, obj=None):
        if obj is None:
            obj = IndexedScale
        super().__init__(obj, scale=0., inds=())

    def readFromStream(self, strm):
        scale = self._readBuff(strm)
        self._obj.scale = scale

    def writeToStream(self, strm):
        dt = self._gen_dt()
        strm.write(np.array([(len(self._obj.inds), self._obj.scale, self._obj.inds)], dtype=dt).tobytes())


# ----------------------------------------
#    Layers

class LayerCache(VizCache):

    # draw, count, exts, id, volatile
    H_DT = np.dtype([('draw','<u4'), ('count','<u4'), ('id','<i4'), ('volatile','<u4')])

    GC_CODES = IntEnum('GC_CODES','V4 CR CI',start=0)

    def __init__(self,scene,layer,**kwargs):
        kwargs.setdefault('id',0)
        super().__init__(layer,**kwargs)
        self._scene = scene
        self._recId = -1

    def peekHeader(self,strm):
        lastpos = strm.tell()
        buff = np.fromfile(strm, LayerCache.H_DT, 1)[0]
        ret = {'draw':bool(buff['draw']),
               'count':int(buff['count']),
               'id':int(buff['id']),
               'volatile':bool(buff['volatile']),
               }
        strm.seek(lastpos)
        return ret

    def skipInStream(self,strm):

        # cache header as obj, since we won't need original
        self._obj = self.peekHeader(strm)
        # skip header
        strm.seek(LayerCache.H_DT.itemsize,1)
        hasExts = np.fromfile(strm, np.uint32, 1)[0]

        # skip exts
        if hasExts > 0:
            strm.seek(16, 1)

        self.skipGeomColors(strm)


    def readFromStream(self, strm):
        buff = np.fromfile(strm,LayerCache.H_DT,1)[0]
        rec = self._obj
        rec.draw = bool(buff['draw'])
        rec.count = int(buff['count'])
        self._recId = int(buff['id'])
        rec.id = self._scene.getNextId()
        rec.volatile = bool(buff['volatile'])
        rec.exts=None
        hasExts = np.fromfile(strm,np.uint32,1)[0]
        if hasExts > 0:
            rec.exts = list(np.fromfile(strm,np.float32,4))
        # let subclasses optionally deal with geomcolors
        self.readGeomColors(strm)

    def writeToStream(self,strm):
        rec = self._obj
        buff = np.array([(rec.draw,
                         rec.count,
                         rec.id,
                         rec.volatile)],dtype=LayerCache.H_DT)
        strm.write(buff.tobytes())
        strm.write(np.array([1 if rec.exts is not None else 0],dtype=np.uint32).tobytes())
        if rec.exts is not None:
            strm.write(np.array(rec.exts,dtype=np.float32).tobytes())
        self.writeGeomColors(strm)

    def readGeomColors(self,strm):

        CHR_DT = np.dtype('<u4')
        count = np.fromfile(strm,C_DT,1)[0]
        if count>0:
            gmCode = np.fromfile(strm,CHR_DT,1)[0]

            if gmCode == LayerCache.GC_CODES.V4:
                buff = np.fromfile(strm,V4_DT,count)
                self._obj.geomColors=[glm.vec4(b) for b in buff]

            else:
                if gmCode == LayerCache.GC_CODES.CR:
                    procGen = ColorRangeCache
                elif gmCode == LayerCache.GC_CODES.CI:
                    procGen = IndexedColorCache
                else:
                    raise GaiaGLCacheException(f"Unrecognized geomColor code: {gmCode}")
                self._obj.geomColors=[]
                for _ in range(count):
                    proc = procGen()
                    proc.readFromStream(strm)
                    self._obj.geomColors.append(proc.obj)


    def skipGeomColors(self,strm):
        CHR_DT = np.dtype('<u4')
        count = np.fromfile(strm, C_DT, 1)[0]
        if count > 0:
            gmCode = np.fromfile(strm, CHR_DT, 1)[0]

            if gmCode == LayerCache.GC_CODES.V4:
                strm.seek(V4_DT.itemsize * count, 1)
            else:
                if gmCode == LayerCache.GC_CODES.CR:
                    procGen = ColorRangeCache
                elif gmCode == LayerCache.GC_CODES.CI:
                    procGen = IndexedColorCache
                else:
                    raise GaiaGLCacheException(f"Unrecognized geomColor code: {gmCode}")
                for _ in range(count):
                    proc = procGen()
                    proc.skipInStream(strm)

    def writeGeomColors(self,strm):

        CHR_DT = np.dtype('<u4')
        strm.write(np.array([len(self._obj.geomColors)],dtype=C_DT).tobytes())
        if len(self._obj.geomColors)>0:
            # check to see what the first object is.
            sample=self._obj.geomColors[0]
            if isinstance(sample,glm.vec4):
                strm.write(np.array([LayerCache.GC_CODES.V4],dtype=CHR_DT).tobytes())
                unpackedcolors = [(*rgba,) for rgba in self._obj.geomColors]
                strm.write(np.array(unpackedcolors,dtype=V4_DT).tobytes())
            else:
                if isinstance(sample,ColorRange):
                    clrCode = LayerCache.GC_CODES.CR
                    progProc = ColorRangeCache
                elif isinstance(sample,IndexedColor):
                    clrCode = LayerCache.GC_CODES.CI
                    progProc = IndexedColorCache
                else:
                    raise GaiaGLCacheException(f"Unrecognized GeomColor type: {type(sample)}")

                strm.write(np.array([clrCode], dtype=CHR_DT).tobytes())
                for gc in self._obj.geomColors:
                    serializer = progProc(gc)
                    serializer.writeToStream(strm)

    @property
    def idmap(self):
        return self._recId,self._obj.id if self._obj is not None else -1
    # @property
    # def writeSize(self):
    #     return LayerCache.H_DT.itemsize

class PolyLayerCache(LayerCache):

    POLY_DT = np.dtype([('drawGrid','<u4'),('fillGrid','<u4'),('useFillAttrVals','<u4'),
                        ('line_thickness','<u4'),('gridColor','<4f4')])

    def __init__(self,scene,layer=None):
        if layer is None:
            layer = PolyLayerRecord
        super().__init__(scene,layer)

    # TODO: Add support for ref and gradTexes
    #       This will likely involve pointing to another record in archive
    def readFromStream(self, strm):
        super().readFromStream(strm)

        buff = np.fromfile(strm,PolyLayerCache.POLY_DT,1)[0]
        rec = self._obj
        rec.drawGrid = bool(buff['drawGrid'])
        rec.fillGrid = bool(buff['fillGrid'])
        rec.useFillAttrVals = bool(buff['useFillAttrVals'])
        rec.line_thickness = int(buff['line_thickness'])
        rec.gridColor =glm.vec4(buff['gridColor'])
        rec.needsAdjacency=False
        grpCount, = np.fromfile(strm,C_DT,1)
        rec.groups = []
        for _ in range(grpCount):
            ringCount, = np.fromfile(strm,C_DT,1)
            rec.groups.append([tuple(x) for x in np.fromfile(strm, GROUP_DT, ringCount)])

        # read count and populate stream
        verts = np.fromfile(strm,PT_DT,self._obj.vertCount)

        rec.selectedRecs = np.zeros(rec.count,np.uint32)
        self._scene._loadPolyLayer(rec,rec.exts,verts)


    def skipInStream(self,strm):
        super().skipInStream(strm)

        strm.seek(PolyLayerCache.POLY_DT.itemsize,1)
        vertCount = 0
        grpCount, = np.fromfile(strm, C_DT, 1)
        for _ in range(grpCount):
            ringCount, = np.fromfile(strm, C_DT, 1)
            sizes=[tuple(x)[1] for x in np.fromfile(strm, GROUP_DT, ringCount)]
            vertCount+=sum(sizes)

        # read count and populate stream
        strm.seek(PT_DT.itemsize*vertCount,1)

    def writeToStream(self, strm):
        super().writeToStream(strm)
        rec = self._obj
        buff = np.array([(rec.drawGrid,
                         rec.fillGrid,
                         rec.useFillAttrVals,
                         rec.line_thickness,
                         rec.gridColor)],dtype=PolyLayerCache.POLY_DT)
        strm.write(buff.tobytes())

        strm.write(np.array([len(rec.groups)],dtype=C_DT).tobytes())
        for ring in rec.groups:
            strm.write(np.array([len(ring)],dtype=C_DT).tobytes())
            strm.write(np.array([*ring], dtype=GROUP_DT).tobytes())
        self._scene.dumpVertsToStream(rec,strm)

    # @property
    # def writeSize(self):
    #     return super().writeSize # +


class PointLayerCache(LayerCache):
    PTATTR_DT = np.dtype([('ptSize', '<f4'),('glyphCode','<u4'),('colorMode','<u4'),('scaleByValue','<u4'),('scaleMinSize','<f4'),
                          ('scaleMaxSize','<f4'),('clampColorToRange','<u4'),('valueBounds','<2f4')])

    def __init__(self,scene,layer=None):
        if layer is None:
            layer = PointLayerRecord
        super().__init__(scene,layer)

    # TODO: Add support for gradTexId, gradient, ptSelBuff and auxColorBuff, if needed

    def readFromStream(self, strm):
        super().readFromStream(strm)

        buff = np.fromfile(strm, PointLayerCache.PTATTR_DT, 1)[0]
        rec = self._obj # PointLayerRecord
        rec.ptSize = float(buff['ptSize'])
        if rec.ptSize<=0:
            rec.ptSize=None
        rec.glyphCode=chr(buff['glyphCode'])
        if rec.glyphCode==0:
            rec.glyphCode=None
        rec.colorMode = POINT_FILL(int(buff['colorMode']))
        rec.scaleByValue = bool(buff['scaleByValue'])
        rec.scaleMinSize = float(buff['scaleMinSize'])
        rec.scaleMaxSize = float(buff['scaleMaxSize'])
        rec.clampColorToRange = bool(buff['clampColorToRange'])
        rec.valueBounds = glm.vec2(buff['valueBounds'])

        indCount = np.fromfile(strm,C_DT,1)[0]
        rec.indexedGlyphs=[None]*indCount
        loader = IndexedGlyphCache()
        for i in range(indCount):
            loader.readFromStream(strm)
            rec.indexedGlyphs[i]=loader.obj

        indCount = np.fromfile(strm, C_DT, 1)[0]
        rec.indexedScales = [None] * indCount
        loader = IndexedScaleCache()
        for i in range(indCount):
            loader.readFromStream(strm)
            rec.indexedScales[i] = loader.obj

        verts = np.fromfile(strm, PT_DT, self._obj.vertCount)

        # for now, just manually populate selected recs
        rec.selectedRecs = np.zeros(rec.count,np.uint32)
        self._scene._loadPointLayer(rec,rec.exts,verts)

    def skipInStream(self,strm):
        super().skipInStream(strm)
        strm.seek(PointLayerCache.PTATTR_DT.itemsize,1)
        skipper = IndexedGlyphCache()
        skipper.skipInStream(strm)
        skipper = IndexedScaleCache()
        skipper.skipInStream(strm)
        strm.seek(PT_DT.itemsize*self._obj['count'],1)

    def writeToStream(self,strm):
        super().writeToStream(strm)
        rec = self._obj # PointLayerRecord
        buff = np.array([(rec.ptSize if rec.ptSize is not None else 0.,
                          ord(rec.glyphCode) if rec.glyphCode is not None else 0,
                          int(rec.colorMode),
                          rec.scaleByValue,
                          rec.scaleMinSize,
                          rec.scaleMaxSize,
                          rec.clampColorToRange,
                          glm.vec2(rec.valueBounds)
                          )], dtype=PointLayerCache.PTATTR_DT)
        strm.write(buff.tobytes())
        strm.write(np.array([len(self._obj.indexedGlyphs)], dtype=C_DT).tobytes())
        for ig in self.obj.indexedGlyphs:
            serializer=IndexedGlyphCache(ig)
            serializer.writeToStream(strm)

        strm.write(np.array([len(self._obj.indexedScales)], dtype=C_DT).tobytes())
        for isc in self.obj.indexedScales:
            serializer= IndexedScaleCache(isc)
            serializer.writeToStream(strm)

        self._scene.dumpVertsToStream(rec, strm)

class LineLayerCache(LayerCache):

    LINE_DT = np.dtype([('line_thickness','<u4'),('colorMode','<u4'),
                        ('lowVal','<f4'),('highVal','<f4')])

    def __init__(self,scene,layer=None):
        if layer is None:
            layer = LineLayerRecord
        super().__init__(scene,layer,linegroups=[])

    def skipInStream(self, strm):
        super().skipInStream(strm)
        vertCount = 0
        grpCount, = np.fromfile(strm, C_DT, 1)
        for _ in range(grpCount):
            _, count = np.fromfile(strm, GROUP_DT)
            vertCount += count

        # read count and populate stream
        strm.seek(PT_DT.itemsize * vertCount, 1)

    # TODO: Add support for ref and gradTexes
    #       This will likely involve pointing to another record in archive
    def readFromStream(self, strm):
        super().readFromStream(strm)

        buff = np.fromfile(strm,LineLayerCache.LINE_DT,1)[0]
        rec = self._obj
        rec.line_thickness = int(buff['line_thickness'])
        rec.colorMode = LINE_FILL(int(buff['colorMode']))
        rec.lowVal = float(buff['lowVal'])
        rec.highVal = float(buff['highVal'])
        rec.needsAdjacency=False

        grpCount, = np.fromfile(strm,C_DT,1)
        rec.groups = []
        for _ in range(grpCount):
            rec.groups.append(np.fromfile(strm, GROUP_DT,1)[0])

        # read count and populate stream
        verts = np.fromfile(strm,PT_DT,self._obj.vertCount)
        extraVals = None
        self._scene._loadLineLayer(rec,rec.exts,verts,extraVals)

    def writeToStream(self, strm):
        super().writeToStream(strm)
        rec = self._obj
        buff = np.array([(rec.line_thickness,
                          int(rec.colorMode),
                          rec.lowVal,
                          rec.highVal,
                        )], dtype=LineLayerCache.LINE_DT)
        strm.write(buff.tobytes())
        strm.write(np.array([len(rec.groups)], dtype=C_DT).tobytes())
        for g in rec.groups:
            strm.write(np.array([tuple(g)], dtype=GROUP_DT).tobytes())
        self._scene.dumpVertsToStream(rec, strm)

class RasterLayerCache(LayerCache):

    # TODO: ensure this works.
    # most of the time, better to use non-cached versions (smaller on disk)
    def __init__(self, scene, layer=None, **kwargs):
        if layer is None:
            layer=RasterLayerRecord
        super().__init__(scene, layer, **kwargs)

    def readFromStream(self, strm):
        super().readFromStream(strm)

        internalFrmt, pxdata = self._scene.loadTexFromStream(strm)
        self._scene._loadRasterLayer(pxdata,internalFrmt,self._obj)


    def skipInStream(self,strm):
        super().skipInStream(strm)
        self._scene.loadTexFromStream(strm,skip=True)


    def writeToStream(self, strm):
        super().writeToStream(strm)

        self._scene.dumpTexToStream(self.obj,strm)



class RasterIndexLayerCache(RasterLayerCache):
    # presently not used
    ...


class ReferenceLayerCache(LayerCache):

    # TODO: in situ testing
    RL_DT = np.dtype([('id','<u4'),('src','<u4'),('pureAlias','<u4')])

    def __init__(self, scene, layer=None):
        if layer is None:
            layer = ReferenceRecord
        super().__init__(scene, layer,id=-1,srcRecord=-1)

    def readFromStream(self, strm):
        # do not call super(); most of those attributes are deleted
        buff = np.fromfile(strm,ReferenceLayerCache.RL_DT,1)[0]
        rec = self._obj
        rec.id = int(buff['id'])
        rec.srcRecord = int(buff['src'])
        rec._pureAlias = bool(buff['pureAlias'])

        if not rec._pureAlias:
            self.readGeomColors(strm)

        self._scene._loadReferenceLayer(rec)


    def skipInStream(self,strm):
        buff = np.fromfile(strm, ReferenceLayerCache.RL_DT, 1)[0]
        pureAlias = bool(buff['pureAlias'])

        if not pureAlias:
            self.skipGeomColors(strm)


    def writeToStream(self, strm):

        # do not call super(); most of those attributes are deleted
        rec = self._obj
        buff = np.array([(rec.id,rec.srcRecord.id,rec._pureAlias,)],dtype=ReferenceLayerCache.RL_DT)
        strm.write(buff.tobytes())
        if not rec._pureAlias:
            self.writeGeomColors(strm)


# ----------------------------------------
#    Layer stack

class LayerStackCache(object):

    LYR_TYPE = IntEnum('LYR_TYPE','POLY POINT REF RASTER LINE',start=1)

    VERSIZE_DT = np.dtype('<4u4')

    _recCacheMap = {PolyLayerRecord   :( LYR_TYPE.POLY,PolyLayerCache),
                    PointLayerRecord  :( LYR_TYPE.POINT,PointLayerCache),
                    ReferenceRecord   :( LYR_TYPE.REF,ReferenceLayerCache),
                    RasterLayerRecord :( LYR_TYPE.RASTER,RasterLayerCache),
                    LineLayerRecord   :( LYR_TYPE.LINE,LineLayerCache),
                 }
    _typCacheMap = {LYR_TYPE.POLY  : PolyLayerCache,
                    LYR_TYPE.POINT : PointLayerCache,
                    LYR_TYPE.REF   : ReferenceLayerCache,
                    LYR_TYPE.RASTER: RasterLayerCache,
                    LYR_TYPE.LINE  : LineLayerCache,
                 }

    def __init__(self,scene):
        self._scene = scene
        self._indexMap = {}

    def saveLayersToFile(self,path):

        with open(path,'wb') as outFile:

            # write version and stack count
            outFile.write(np.array([(*GAIAVIZ_VERSION,self._scene.layerCount)],LayerStackCache.VERSIZE_DT).tobytes())

            # save layers in order
            for lyr in self._scene.layerIter():

                typeId,cacheType= LayerStackCache._recCacheMap[type(lyr)]
                outFile.write(np.array([typeId],dtype=np.uint32).tobytes())
                cache=cacheType(self._scene,lyr)
                cache.writeToStream(outFile)


    def openLayersFromFile(self,path,filter=None):

        with open(path,'rb') as inFile:
            self._indexMap.clear()

            # load version and count
            vers = []*3
            *vers,lyrCount= np.fromfile(inFile,LayerStackCache.VERSIZE_DT,1)[0]

            # Here's where we'd add a version check..
            vCheck=check_version(*vers)
            if vCheck!=0:
                print(f"WARNING: library version ({'.'.join([str(v) for v in GAIAVIZ_VERSION])}) does not match cached version "
                      f"({'.'.join([str(v) for v in vers])}). This may lead to unexpected behavior.")

            for _ in range(lyrCount):
                # first, grab flag indicating layer type
                typeId = np.fromfile(inFile,np.uint32,1)[0]
                cacheType = LayerStackCache._typCacheMap[typeId]
                cache = cacheType(self._scene)

                # peek the header if using filter
                if filter is not None:
                    hdr = cache.peekHeader(inFile)
                    if hdr['id'] not in filter:
                        cache.skipInStream(inFile)
                        continue

                cache.readFromStream(inFile)

                # grab old id, and then add new id
                oldId,newId = cache.idmap
                # cache.obj.id= self._scene.getNextId()
                self._indexMap[oldId] = newId

            # use ID map to update referenceLayerRecords
            for lyr in self._indexMap.values():

                if type(lyr)==ReferenceRecord:
                    src = self._indexMap[lyr.srcRecord]
                    lyr.srcRecord = src
                    lyr.vao = src.vao
                    lyr.buff = src.buff
                    lyr.count = src.count
                    lyr.exts = src.exts
                # add other mappings here...

    def idForKey(self,cache_id):

        if cache_id not in self._indexMap:
            return None
        return self._indexMap[cache_id]
