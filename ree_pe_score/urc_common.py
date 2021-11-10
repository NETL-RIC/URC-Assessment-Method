import sys
import os
import fnmatch
from osgeo import gdal
from .common_utils import *

_gdt_np_map = {
    gdal.GDT_Byte: np.uint8,
    gdal.GDT_UInt16: np.uint16,
    gdal.GDT_Int16: np.int16,
    gdal.GDT_UInt32: np.uint32,
    gdal.GDT_Int32: np.int32,
    gdal.GDT_Float32: np.float32,
    gdal.GDT_Float64: np.float64,
    gdal.GDT_CInt16: np.int16,
    gdal.GDT_CInt32: np.int32,
    gdal.GDT_CFloat32: np.float32,
    gdal.GDT_CFloat64: np.float64,
}


class RasterGroup(object):

    def __init__(self,**kwargs):

        self._rasters= {}
        self._cached_ref=None

        notFound = []
        for k,v in kwargs.items():
            try:
                self.add(k,v)
            except RuntimeError:
                notFound.append(v)
        if len(notFound)>0:
            raise RuntimeError("The following files were not found:"+",".join(notFound))

    def __repr__(self):
        return f'Rasters={", ".join(self.rasterNames)}'

    def __getitem__(self, item):
        return self._rasters[item]

    def __setitem__(self, key, value):
        self.add(key,value)

    def __delitem__(self, key):
        if self._rasters[key]==self._cached_ref:
            self._cached_ref=None
        del self._rasters[key]

    def items(self):
        return self._rasters.items()

    def add(self, id, path_or_ds):

        if id in self._rasters:
            raise KeyError(f"Raster with {id} exists; explicitly delete before adding")

        if isinstance(path_or_ds, gdal.Dataset):
            self._rasters[id]=path_or_ds
            return
        ds = gdal.Open(path_or_ds)
        # if existing rasters, check for consistancy
        if len(self._rasters)>0:
            test=self._rasters[tuple(self._rasters.keys())[0]]
            ds_gtf = ds.GetGeoTransform()
            test_gtf = ds.GetGeoTransform()
            if ds.RasterXSize!=test.RasterXSize or ds.RasterYSize != test.RasterYSize \
               or any([ds_gtf[i]!= test_gtf[i] for i in range(6)]):
                raise ValueError(f"The raster '{id}'({path_or_ds}) does not match dimensions of existing entries")
        self._rasters[id]= ds

    def generateHitMap(self,keys=None):
        ret=np.empty([len(self._rasters),self.RasterYSize,self.RasterXSize],dtype=np.uint8)
        if keys is None:
            keys = list(self._rasters.keys())
        keys = sorted(keys)
        for i, k in enumerate(keys):
            ds = self._rasters[k]
            b = ds.GetRasterBand(1).ReadAsArray()
            ndv = ds.GetRasterBand(1).GetNoDataValue()
            # if ndv==0:
            #     # we can skip individual iteration
            #     # NOTE: this will use any value for nonzero, not just 1; this might break
            #     ret[i]=b
            # else:
            for y in range(self.RasterYSize):
                for x in range(self.RasterXSize):
                    ret[i,y,x] = 0 if ndv==b[y,x] else 1
        return keys,ret

    def generateNoDataMask(self):

        mask=np.empty([self.RasterYSize,self.RasterXSize],dtype=np.uint8)
        _,hits = self.generateHitMap()

        for j in range(self.RasterYSize):
            for k in range(self.RasterXSize):
                mask[j,k] = 1 if any(hits[:,j,k]==1) else 0
        return mask

    def copyRasters(self,driver,path,suffix=''):

        if isinstance(driver,str):
            driver=gdal.GetDriverByName(driver)

        copies=[]
        for id,ds in self._rasters.items():
            fullpath = os.path.join(path,id+suffix)
            copies.append(driver.CreateCopy(fullpath,ds))

        return copies

    def _getTestRaster(self):
        if self._cached_ref is None:
            if len(self._rasters)!=0:
                self._cached_ref= self._rasters[tuple(self._rasters.keys())[0]]
        return self._cached_ref

    @property
    def rasterNames(self):
        return sorted(list(self._rasters.keys()))

    @property
    def extents(self):
        ds = self._getTestRaster()
        if ds is None:
            return (0.,)*4
        gtf = ds.GetGeoTransform()
        return (gtf[0],gtf[0]+(gtf[1]*ds.RasterXSize),
                gtf[3],gtf[3]+(gtf[5]*ds.RasterYSize))

    @property
    def projection(self):
        ds = self._getTestRaster()
        if ds is None:
            return ''
        return ds.GetProjection()

    @property
    def geoTransform(self):
        ds = self._getTestRaster()
        if ds is None:
            return (0.,) * 6
        gtf = ds.GetGeoTransform()
        return gtf

    @property
    def spatialRef(self):
        ds = self._getTestRaster()
        if ds is None:
            return None
        return ds.GetSpatialRef()

    @property
    def RasterXSize(self):
        ds = self._getTestRaster()
        if ds is None:
            return 0
        return ds.RasterXSize

    @property
    def RasterYSize(self):
        ds = self._getTestRaster()
        if ds is None:
            return 0
        return ds.RasterYSize


def ListFeatureClassNames(ds, wildCard, first_char=0, last_char=sys.maxsize):
    """Function that creates a list of all unique REE-Coal components in an ESRI GDB Feature Dataset, for use in use in
        calculating PE score from DA and DS databases.

    Args:
        ds (osgeo.gdal.Dataset): The dataset to query.
        wildCard (str): Criteria used to limit the results returned.
        first_char (int,optional): Index of first character to include in the filename.
            Defaults to 0.
        last_char (int,optional): Index of lastcharacter to include in the filename.
            Defaults to position of last character in string.

    Returns:
        list: sorted, non-repeating iterable sequence of layer names based on the WildCard criteria
    """

    fcNames = [ds.GetLayer(i).GetName() for i in range(ds.GetLayerCount())]
    # match against wildcard
    fcNames=[x[first_char:last_char] for x in fnmatch.filter(fcNames,wildCard)]

    return sorted(set(fcNames))


def ListFeatureClasses(ds,wildCard):
    """Function that creates a list of all unique REE-Coal components in an ESRI GDB Feature Dataset, for use in use in
        calculating PE score from DA and DS databases.

    Args:
        ds (osgeo.gdal.Dataset): The dataset to query.
        wildCard (str): Criteria used to limit the results returned.

    Returns:
        list: sorted, non-repeating iterable sequence of Layers based on the WildCard criteria
    """

    fcNames=ListFeatureClassNames(ds, wildCard)

    fcList = []
    for i in range(ds.GetLayerCount()):
        lyr = ds.GetLayer(i)
        if lyr.GetName() in fcNames:
            fcList.append(lyr)


    return fcList


def FindUniqueComponents(gdbDS,prefix):
    """Step 0: find the collections to be used in subsequent steps.

    Args:
        gdbDS (osgeo.gdal.Dataset): Dataset containing features to parse. Expected to
          originate from a file geodatabase (.gdb) file.
        prefix (str): The prefix used to filter returned layers.

    Returns:
        tuple:
            0. list: List of unique layer names.
            1. list: Layer objects corresponding to labels in entry 0.
    """

    # Create a list of all unique code prefixes for the component IDs
    unique_components = ListFeatureClassNames(gdbDS, wildCard=prefix+"*", first_char=0, last_char=14)

    # An array comprising all components and their respective feature classes
    components_data = {}

    # Generate a list of feature classes for each Emplacement Type, Influence Extent, AND Component ID combination
    for uc in unique_components:
        component_datasets = ListFeatureClasses(gdbDS, wildCard=(uc + "*"))

        # Append list to a single array
        components_data[uc] = component_datasets

    return components_data


def RasterizeComponents(src_rasters,gdbDS,component_data,cache_dir=None,mask=None):

    src_gtf = src_rasters.geoTransform
    src_data={'xSize':src_rasters.RasterXSize,
              'ySize':src_rasters.RasterYSize,
              'geotrans':src_rasters.geoTransform,
              'srs':src_rasters.spatialRef,
              'nodata':0,
              'gdType':gdal.GDT_Byte,
              'drvrName':'mem',
              'prefix':'',
              'suffix':'',
              }

    if cache_dir is not None:
        src_data['drvrName'] = 'GTiff'
        src_data['prefix'] = cache_dir
        src_data['suffix'] = '.tif'

    outRasters=RasterGroup()
    for id,fc_list in component_data.items():
        print(f'Rasterizing {id}...')
        rstr = Rasterize(id, fc_list,gdbDS, **src_data)
        outRasters[id] = rstr
        if mask is not None:
            b=rstr.GetRasterBand(1)
            raw = b.ReadAsArray()
            raw[mask==0]=src_data['nodata']
            b.WriteArray(raw)

    return outRasters


def GenDomainHitMaps(src_rasters):
    hitmaps = {}
    for k in ('ld', 'ud', 'sd'):

        print(f'Separating {k} domains...')
        srcBand = src_rasters[k].GetRasterBand(1)
        _, maxVal = srcBand.ComputeRasterMinMax(1)
        maxVal = int(maxVal)
        ndVal = srcBand.GetNoDataValue()
        hitList = [False] * (maxVal + 1)
        # separate values out for individual domains
        subBuffs = np.zeros([maxVal + 1, src_rasters.RasterYSize, src_rasters.RasterXSize], dtype=np.uint8)
        srcBuff = srcBand.ReadAsArray()
        for i in range(src_rasters.RasterYSize):
            for j in range(src_rasters.RasterXSize):
                px = srcBuff[i, j]
                if px != ndVal:
                    subBuffs[px, i, j] = 1
                    hitList[px] = True

        # cache hitmaps
        hitmaps[k] = (subBuffs,hitList)
    return hitmaps


def GenDomainIndexRasters(src_rasters, as_distance, cache_dir=None, mask=None):

    src_data = {'gdType': gdal.GDT_Float32,
                'drvrName': 'mem',
                'prefix': '',
                'suffix': '',
                }
    if as_distance:
        src_data['mask']= mask

    if cache_dir is not None:
        src_data['drvrName'] = 'GTiff'
        src_data['prefix'] = cache_dir
        src_data['suffix'] = '.tif'

    hitmaps = GenDomainHitMaps(src_rasters)

    outRasters = RasterGroup()


    # scratch buffer
    drvr = gdal.GetDriverByName("mem")
    scratchDS = drvr.Create("scratch",src_rasters.RasterXSize,src_rasters.RasterYSize,1,gdal.GDT_Int32)
    scratchDS.SetGeoTransform(src_rasters.geoTransform)
    scratchDS.SetSpatialRef(src_rasters.spatialRef)
    scratchBand = scratchDS.GetRasterBand(1)
    scratchBand.SetNoDataValue(0)

    for k,(subBuffs,hitList) in hitmaps.items():

        print(f'{"Distancing for" if as_distance else "Isolating"} {k} domains...')
        # cache hitmaps
        hitmaps[k] = subBuffs

        # build distances for each domain
        for i in range(subBuffs.shape[0]):
            if not hitList[i]:
                continue
            scratchBand.WriteArray(subBuffs[i])
            id = f'{k}_{i}'

            if as_distance:
                rstr = RasterDistance(id,scratchDS, **src_data)
            else:
                rstr = RasterCopy(id,scratchDS,**src_data)
            outRasters[id] = rstr

    return outRasters,hitmaps


def FindDomainComponentRasters(domDistRasters,hitMaps,testRasters,cache_dir=None):

    comboRasters = RasterGroup()
    fixedArgs = {
                'drvrName': 'mem',
                'prefix': '',
                'suffix': '',
                'comboRasters':comboRasters,
                'domDistRasters':domDistRasters,
                }

    if cache_dir is not None:
        fixedArgs['drvrName'] = 'GTiff'
        fixedArgs['prefix'] = cache_dir
        fixedArgs['suffix'] = '_domain_component.tif'

    for id,srcDS in testRasters.items():
        domKey = id[6:8].lower()
        if domKey not in hitMaps:
            continue
        testBand = srcDS.GetRasterBand(1)
        testBuff = testBand.ReadAsArray()
        nd = testBand.GetNoDataValue()
        hm = hitMaps[domKey]
        found= set() # {x for x in testBand.ReadAsArray().ravel() if x!=nd}
        for i in range(domDistRasters.RasterYSize):
            for j in range(domDistRasters.RasterXSize):
                v = testBuff[i,j]
                if v!=nd and v!=0:
                    for h in range(hm.shape[0]):
                        if hm[h,i,j]!=0:
                            found.add(h)
        CombineDomDistRasters(found,domKey,id,**fixedArgs)
    return comboRasters


def CombineDomDistRasters(found,domKey,compName,domDistRasters,comboRasters,prefix='',suffix='',drvrName='mem'):

    path = os.path.join(prefix,compName) + suffix
    outND = np.inf
    outBuff = np.full([domDistRasters.RasterYSize,domDistRasters.RasterXSize],outND,dtype=np.float32)
    for index in found:
        ds = domDistRasters[f'{domKey}_{index}']
        b = ds.GetRasterBand(1)
        inND = b.GetNoDataValue()
        readBuff = b.ReadAsArray()
        for i in range(ds.RasterYSize):
            for j in range(ds.RasterXSize):
                if readBuff[i,j]==inND:
                    continue
                if outBuff[i,j]==outND or outBuff[i,j]>readBuff[i,j]:
                    outBuff[i, j] = readBuff[i, j]

    drvr = gdal.GetDriverByName(drvrName)
    print("Combine: writing "+path)
    outDS = drvr.Create(path, domDistRasters.RasterXSize, domDistRasters.RasterYSize, 1, gdal.GDT_Float32)
    outDS.SetGeoTransform(domDistRasters.geoTransform)
    outDS.SetSpatialRef(domDistRasters.spatialRef)
    outBand = outDS.GetRasterBand(1)
    outBand.SetNoDataValue(outND)
    outBand.WriteArray(outBuff)
    comboRasters.add(compName,outDS)


def NormMultRasters(implicits,explicits,cache_dir=None):

    multRasters = RasterGroup()

    kwargs = {'geotrans':implicits.geoTransform,
              'spatRef': implicits.spatialRef,
              'drvrName':'mem'
              }

    prefix=''
    suffix=''
    if cache_dir is not None:
        kwargs['drvrName'] = 'GTiff'
        prefix = cache_dir
        suffix = '_norm_product.tif'

    for k in implicits.rasterNames:
        imp = implicits[k]
        exp = explicits[k]

        normImp,impND=normalizeRaster(imp)
        normExp,expND=normalizeRaster(exp)

        id = os.path.join(prefix,k)+suffix
        multRasters[k]=MultBandData(normImp,normExp,id,impND,expND,**kwargs)

    return multRasters


def Rasterize(id, fc_list, inDS, xSize, ySize, geotrans, srs, drvrName="mem", prefix='', suffix='', nodata=-9999,
              gdType=gdal.GDT_Int32):
    path = os.path.join(prefix, id) + suffix
    drvr = gdal.GetDriverByName(drvrName)
    ds = drvr.Create(path, xSize, ySize, 1, gdType)

    ds.SetGeoTransform(geotrans)
    ds.SetSpatialRef(srs)
    b = ds.GetRasterBand(1)
    b.SetNoDataValue(nodata)
    fill = np.full([ySize, xSize], nodata, dtype=_gdt_np_map[gdType])
    b.WriteArray(fill)

    ropts = gdal.RasterizeOptions(
        layers=[fc.GetName() for fc in fc_list]
    )
    gdal.Rasterize(ds, inDS, options=ropts)

    return ds


def RasterCopy(id, inDS, drvrName="mem", prefix='', suffix='', gdType=gdal.GDT_Float32):
    path = os.path.join(prefix, id) + suffix
    drvr = gdal.GetDriverByName(drvrName)

    ds = drvr.CreateCopy(path, inDS)
    return ds


def RasterDistance(id, inDS, drvrName="mem", prefix='', suffix='', mask=None, distThresh=None, gdType=gdal.GDT_Float32):
    path = os.path.join(prefix, id) + suffix
    drvr = gdal.GetDriverByName(drvrName)
    ds = drvr.Create(path, inDS.RasterXSize, inDS.RasterYSize, 1, gdType)

    inBand = inDS.GetRasterBand(1)

    ds.SetGeoTransform(inDS.GetGeoTransform())
    ds.SetSpatialRef(inDS.GetSpatialRef())
    outBand = ds.GetRasterBand(1)
    outND = np.inf  # NOTE: don't use NaN here; it complicates later comparisons
    outBand.SetNoDataValue(outND)
    # fill = np.full([inDS.RasterYSize, inDS.RasterXSize], nodata, dtype=_gdt_np_map[gdType])
    # outBand.WriteArray(fill)

    argStr = "DISTUNITS=GEO"
    if distThresh is not None:
        argStr += f" MAXDIST={distThresh}"
    gdal.ComputeProximity(inBand, outBand, [argStr])

    # do some corrections
    buffer = outBand.ReadAsArray()
    rBuff = buffer.ravel()
    # replace nodatas with 0 distance
    rBuff[rBuff == outND] = 0

    # apply mask if provided
    if mask is not None:
        buffer[mask == 0] = outND

    outBand.WriteArray(buffer)
    return ds


def normalizeRaster(inRast, flip=True):
    band = inRast.GetRasterBand(1)
    ndVal = band.GetNoDataValue()
    raw = band.ReadAsArray()
    out = np.full_like(raw, ndVal, dtype=raw.dtype)

    # grab 1d views to simplify parsing
    raw1d = raw.ravel()
    out1d = out.ravel()

    # cant use gdal.band.ComputeRasterMinMax(),since it breaks if raster is empty
    minVal = np.inf
    maxVal = -np.inf
    for i in range(len(raw1d)):
        if raw1d[i] != ndVal:
            minVal = min(minVal, raw1d[i])
            maxVal = max(maxVal, raw1d[i])
    ext = maxVal - minVal

    if maxVal != -np.inf or minVal != np.inf:

        for i in range(len(raw1d)):
            if raw1d[i] != ndVal:
                if ext != 0.:
                    out1d[i] = (raw1d[i] - minVal) / ext
                else:
                    # in the case were there is only a singular value,
                    # assume that distance is 0
                    out1d[i] = 0

                if flip:
                    out1d[i] = 1 - out1d[i]
    else:
        out = raw
    return out, ndVal


def MultBandData(data1, data2, id, nd1, nd2, geotrans, spatRef, drvrName='mem'):
    prod = np.full_like(data1, nd1, dtype=np.float32)
    prod1D = prod.ravel()

    for i, (d1, d2) in enumerate(zip(data1.ravel(), data2.ravel())):
        if d1 != nd1 and d2 != nd2:
            prod1D[i] = d1 * d2

    drvr = gdal.GetDriverByName(drvrName)
    outDS = drvr.Create(id, data1.shape[1], data1.shape[0], 1, gdal.GDT_Float32)
    outDS.SetGeoTransform(geotrans)
    outDS.SetSpatialRef(spatRef)
    b = outDS.GetRasterBand(1)
    b.SetNoDataValue(nd1)
    b.WriteArray(prod)
    return outDS


def buildPandasDataframe(indexRasters,daRasters):
    lgDS = indexRasters['lg']
    lgArray=lgDS.GetRasterBand(1).ReadAsArray()
    lgNd = lgDS.GetRasterBand(1).GetNoDataValue()
    columns,hitmap = daRasters.generateHitMap()

    df = pd.DataFrame(data=None, columns=['LG_index']+columns)
    df['LG_index']=lgArray.ravel()
    df.set_index('LG_index', inplace=True)

    # hitmap dimensions are (rasters,y,x)
    # column = rasters
    # LG/row = y*RasterXSize + x
    # reshape to make parsing easier; this should preserve index ordering
    hitmap1D=hitmap.reshape([hitmap.shape[0],hitmap.shape[1]*hitmap.shape[2]])
    for i,lbl in enumerate(columns):
        df[lbl]=hitmap1D[i]

    # drop noData cells
    df.drop(index=lgNd,inplace=True)
    return df

def DataFrameToRasterGroup(df,lgInd,cols=None,gdtype=gdal.GDT_Float32):

    if cols is None:
        cols = list(df.columns)
    lgBand = lgInd.GetRasterBand(1)
    lgNoData = lgBand.GetNoDataValue()
    lgBuff = lgBand.ReadAsArray()
    lgFlat = lgBuff.ravel()
    drRasters = RasterGroup()

    for c in cols:
        slice = df[c]
        outBuff=np.array(lgBuff,dtype=_gdt_np_map[gdtype])
        flatBuff=outBuff.ravel()
        for i in range(len(flatBuff)):
            if lgFlat[i]!=lgNoData:
                flatBuff[i]=slice[lgFlat[i]]
        ds=writeRaster(lgInd, outBuff, c,'mem', gdtype, nodata=lgNoData)
        drRasters.add(c,ds)
    return drRasters
