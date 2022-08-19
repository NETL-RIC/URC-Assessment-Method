import sys
import os
import fnmatch

import numpy as np
from osgeo import gdal
from .common_utils import *
import pandas as pd



class RasterGroup(object):
    """Container for storing Rasters which share the same dimensions and geotransformations.

    Keyword Args:
        kwargs: Any provide named arguments are expected to have a gdal.Dataset as a value, and the key will
          be reused as the reference id.
    """

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

    def __contains__(self, item):
        return item in self._rasters

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
        """Equivalent to `dict.items`.

        Returns:
            dict_items: A key,value generator.
        """
        return self._rasters.items()

    def add(self, id, path_or_ds):
        """Add a new raster to the dataset.

        Args:
            id (str): The label to apply to the raster dataset.
            path_or_ds (str or gdal.Dataset): Either a path to a raster, or a loaded raster Dataset.

        Raises:
            KeyError: If a raster with the value `id` already exists in the group.
            ValueError: If there are existing rasters in the collection and the new raster does not match
               the dimensions or geotransformation of the existing rasters.
        """
        if id in self._rasters:
            raise KeyError(f"Raster with {id} exists; explicitly delete before adding")

        if isinstance(path_or_ds, gdal.Dataset):
            ds=path_or_ds
        else:
            ds = gdal.Open(path_or_ds)

        # if existing rasters, check for consistancy
        if not self._checkConsistancy(ds):
            raise ValueError(f"The raster '{id}'({path_or_ds}) does not match dimensions of existing entries")
        self._rasters[id]= ds

    def generateHitMap(self,keys=None):
        """Generate a map of presence/absence of data for each raster in group.

        Args:
            keys (list,optional): A list of rasters to include in hitmap generation. If `None`,
              then include all rasters.

        Returns:
            tuple: A list of keys of the rasters included in the analysis, in the order of their inclusion in the
              hitmap, followed by a 3d array representing the hitmap of all included rasters.
              Dimensions are (raster,y,x).
        """

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
        """Generate a noData mask for the combination of all included rasters.

        Returns:
            numpy.ndarray: 2D array of an included raster dimension, denoting which cells are valid (1) or nodata (0).
        """
        mask=np.empty([self.RasterYSize,self.RasterXSize],dtype=np.uint8)
        _,hits = self.generateHitMap()

        for j in range(self.RasterYSize):
            for k in range(self.RasterXSize):
                mask[j,k] = 1 if any(hits[:,j,k]==1) else 0
        return mask

    def copyRasters(self,driver,path,suffix=''):
        """Copy all the rasters in this group using the provided information.

        Args:
            driver (str or gdal.Driver): Either the name of the driver to use for copying, or the Driver object itself.
            path (str): Path to parent directory to write out each raster; acts as label with drivers that don't
               require paths (such as "MEM").
            suffix (str,optional): The tail to apply to the filepath; typically this is a file extension. Can be omitted.

        Returns:
            list: List of newly created gdal.Datasets. This return value can be ignored if just concerned with
              performing a write-only operation.
        """
        if isinstance(driver,str):
            driver=gdal.GetDriverByName(driver)

        copies=[]
        for id,ds in self._rasters.items():
            fullpath = os.path.join(path,id+suffix)
            copies.append(driver.CreateCopy(fullpath,ds))

        return copies

    def update(self,other):
        """Add content from another RasterGroup. This effectively calls add()
        on all contents of `other`.

        Args:
            other (RasterGroup): The other raster to extract values from.

        Raises:
            ValueError: If `other` is not of type `RasterGroup`.
        """
        if not isinstance(other,RasterGroup):
            raise ValueError("'other' must be of type RasterGroup")
        for k,r in other.items():
            self.add(k,r)

    def clipWithRaster(self,clipRaster,shrinkToFit=False):

        if not self._checkConsistancy(clipRaster):
            raise ValueError("Clipping raster must match dimensions of RasterGroup")

        clipBand = clipRaster.GetRasterBand(1).ReadAsArray()
        clipFlat = clipBand.ravel()
        # for each raster, keep mask where 1, else mark as nodata
        for v in self._rasters.values():
            b = v.GetRasterBand(1).ReadAsArray()
            nd = v.GetRasterBand(1).GetNoDataValue()
            bFlat = b.ravel()

            for i in range(len(clipFlat)):
                if clipFlat[i]==0:
                    bFlat[i]=nd
            v.GetRasterBand(1).WriteArray(b)

        # TODO: Shrink to fit is disabled because gdal.Translate does not appear
        # to subwindow properly. Come up with another scheme (maybe warp?)

        # if shrinkToFit:
        #     # if shrink to fit:
        #
        #     # grab group mask
        #     ndMask=self.generateNoDataMask()
        #     # find all exts
        #     oX = 0
        #     oY = 0
        #     w = self.RasterYSize
        #     h = self.RasterXSize
        #
        #     for y in range(ndMask.shape[0]):
        #         if any(ndMask[y,:]!=0):
        #             break
        #         oY+=1
        #
        #     for x in range(ndMask.shape[1]):
        #         if any(ndMask[:, x] != 0):
        #             break
        #         oX += 1
        #
        #     w-=oX
        #     h-=oY
        #     for y in range(ndMask.shape[0]-1,0,-1):
        #         if any(ndMask[y,:]!=0):
        #             break
        #         h-=1
        #
        #     for x in range(ndMask.shape[1]-1,0,-1):
        #         if any(ndMask[:, x] != 0):
        #             break
        #         w -= 1
        #
        #     # if smaller, translate all rasters
        #     print(f'({oX}, {oY})')
        #     print(f'w: {w}')
        #     print(f'h: {h}')
        #     if any((oX > 0, oY >0,w<self.RasterXSize,h<self.RasterYSize)):
        #         for k in list(self._rasters.keys()):
        #             self._rasters[k] = gdal.Translate(k,self._rasters[k],srcWin=[oX,oY,w,h])

    def calcMaxValues(self,prefix=None,outNoData=-9999):

        vals=[]
        for k,v in self._rasters.items():
            if prefix is not None and not k.startswith(prefix):
                continue

            b = v.GetRasterBand(1).ReadAsArray()
            nd = v.GetRasterBand(1).GetNoDataValue()
            b[b==nd]=-np.inf
            vals.append(b)

        if len(vals)==0:
            return None
        ret=np.stack(vals).max(axis=0)
        ret[ret==-np.inf]=outNoData

        return ret




    def _checkConsistancy(self,ds):
        """..."""
        if len(self._rasters)>0:
            test=self._rasters[tuple(self._rasters.keys())[0]]
            ds_gtf = ds.GetGeoTransform()
            test_gtf = test.GetGeoTransform()
            if ds.RasterXSize!=test.RasterXSize or ds.RasterYSize != test.RasterYSize \
               or any([ds_gtf[i]!= test_gtf[i] for i in range(6)]):
                return False
        return True

    def _getTestRaster(self):
        """Retrieve a raster to use for testing for conformance.

        Returns:
            gdal.Dataset: raster to use for testing, or `None` if RasterGroup is empty.
        """
        if self._cached_ref is None:
            if len(self._rasters)!=0:
                self._cached_ref= self._rasters[tuple(self._rasters.keys())[0]]
        return self._cached_ref

    @property
    def rasterNames(self):
        """list: Alphabetically sorted list of raster ids/names."""
        return sorted(list(self._rasters.keys()))

    @property
    def extents(self):
        """tuple: The shared real-world extents in (x-min,x-max,y-min,y-max) order."""
        ds = self._getTestRaster()
        if ds is None:
            return (0.,)*4
        gtf = ds.GetGeoTransform()
        return (gtf[0],gtf[0]+(gtf[1]*ds.RasterXSize),
                gtf[3],gtf[3]+(gtf[5]*ds.RasterYSize))

    @property
    def geoTransform(self):
        """tuple: The shared geotransformation matrix for all included rasters."""
        ds = self._getTestRaster()
        if ds is None:
            return (0.,) * 6
        gtf = ds.GetGeoTransform()
        return gtf

    @property
    def spatialRef(self):
        """osr.SpatialReference: The spatial reference used by the internal test raster, or `None` if group is empty."""
        ds = self._getTestRaster()
        if ds is None:
            return None
        return ds.GetSpatialRef()
    @property
    def RasterXSize(self):
        """int: The width (in pixels) of all included rasters."""
        ds = self._getTestRaster()
        if ds is None:
            return 0
        return ds.RasterXSize

    @property
    def RasterYSize(self):
        """int: The height (in pixels) of all included rasters."""
        ds = self._getTestRaster()
        if ds is None:
            return 0
        return ds.RasterYSize

    @property
    def emptyRasterNames(self):
        names=[]

        for id,ds in self._rasters.items():
            b=ds.GetRasterBand(1)
            nd=b.GetNoDataValue()
            hit = False
            for v in b.ReadAsArray().ravel():
                if v!=nd:
                    hit = True
                    break
            if not hit:
                # if we get here, raster is empty
                names.append(id)

        return names

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
    """Find the collections to be used in subsequent steps.

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
    """Convert specified vector layers into raster datasets.

    Args:
        src_rasters (RasterGroup): The RasterGroup container to use as frame of reference for conversion.
        gdbDS (gdal.Dataset): Source of vector layers to convert.
        component_data (dict): Id and vector components to Raster.
        cache_dir (str,optional): If present, save generated rasters to the specified folder.
        mask (numpy.ndarray,optional): If present, apply mask to newly created rasters.

    Returns:
        RasterGroup: collection of newly rasterized components.
    """

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
        src_data['opts'] = ['GEOTIFF_KEYS_FLAVOR=ESRI_PE']

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
    """Generate hitmaps for each domain component.

    Args:
        src_rasters (RasterGroup): The index rasters to use for generating the hitmaps.

    Returns:
        dict: Collection of index hitmaps for ld, ud, and sd domains, along with which values were hit.
    """

    hitmaps = {}
    for k in ('ld', 'ud', 'sd'):

        print(f'Separating {k} domains...')
        srcBand = src_rasters[k].GetRasterBand(1)
        _, maxVal = srcBand.ComputeRasterMinMax(0)
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
    """Generate unique rasters for each domain component.

    Args:
        src_rasters (RasterGroup): The rasters to use for domain index generation.
        as_distance (bool): If true, creates domain as a distance from index raster; otherwise,
          creates presence/absence raster.
        cache_dir (str,optional): If present, save generated rasters to the specified folder.
        mask (numpy.ndarray,optional): If present, apply mask to newly created rasters.

    Returns:
        tuple: RasterGroup of newly created rasters, and the associated list of hit values.
    """

    src_data = {
                'drvrName': 'mem',
                'prefix': '',
                'suffix': '',
                }
    if as_distance:
        src_data['mask']= mask
        src_data['gdType']: gdal.GDT_Float32
    if cache_dir is not None:
        src_data['drvrName'] = 'GTiff'
        src_data['prefix'] = cache_dir
        src_data['suffix'] = '.tif'
        src_data['opts'] = ['GEOTIFF_KEYS_FLAVOR=ESRI_PE']

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
    """Find Domain/index overlap for individual components.

    Args:
        domDistRasters (RasterGroup): Rasters containing domain distances.
        hitMaps (dict): key is name of raster in `testRasters`, value is numpy.ndarray as hit map for associated index.
        testRasters (RasterGroup): The domain indices rasters to use for domain expansion.
        cache_dir (str,optional): If present, save generated rasters to the specified folder.

    Returns:
        RasterGroup: The newly created domain-component distance rasters.
    """

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
    """Combine individual domain indices rasters into new raster.

    Args:
        found (set): Collection of domain indices triggered in hitmap.
        domKey (str): The domain key (ie 'ld','ud',or 'sd').
        compName (str): Label or path to apply to newly created raster
        domDistRasters (RasterGroup): Collection of domain distance rasters.
        comboRasters (RasterGroup): The collection to add the newly generated raster to.
        prefix (str,optional): Prefix to apply to `compName` for gdal.Dataset label; this could be a path to a directory
           if raster is being saved to disk.
        suffix (str,optional): Suffix to apply to `compName` for gdal.Dataset label; this could be the file extension
           if raster is being saved to disk.
        drvrName (str,optional): Name of driver to use to create new raster; defaults to "MEM".
    """

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
    opts=[]
    if drvrName.lower()=='gtiff':
        opts=['GEOTIFF_KEYS_FLAVOR=ESRI_PE']
    outDS = drvr.Create(path, domDistRasters.RasterXSize, domDistRasters.RasterYSize, 1, gdal.GDT_Float32,options=opts)
    outDS.SetGeoTransform(domDistRasters.geoTransform)
    outDS.SetSpatialRef(domDistRasters.spatialRef)
    outBand = outDS.GetRasterBand(1)
    outBand.SetNoDataValue(outND)
    outBand.WriteArray(outBuff)
    comboRasters.add(compName,outDS)


def NormMultRasters(implicits,explicits,cache_dir=None):
    """Normalize and multiply rasters; match using input raster names.

    Args:
        implicits (RasterGroup): Rasters containing implicit data.
        explicits (RasterGroup): Rasters containing explicit data.
        cache_dir (str,optional): If present, save generated rasters to the specified folder.

    Returns:
        RasterGroup: The products of normalization and multiplication.
    """

    multRasters = RasterGroup()

    kwargs = {'geotrans':implicits.geoTransform,
              'spatRef': implicits.spatialRef,
              'drvrName':'mem'
              }

    prefix=''
    suffix=''
    if cache_dir is not None:
        kwargs['drvrName'] = 'GTiff'
        kwargs['opts']=['GEOTIFF_KEYS_FLAVOR=ESRI_PE']
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

def NormLGRasters(inRasters,cache_dir=None):
    """"""

    normRasters = RasterGroup()

    geotrans=inRasters.geoTransform
    spatRef=inRasters.spatialRef
    drvrName='mem'
    prefix=''
    suffix=''
    opts=[]
    if cache_dir is not None:
        drvrName = 'GTiff'
        prefix = cache_dir
        suffix = '_norm_distance.tif'
        opts=['GEOTIFF_KEYS_FLAVOR=ESRI_PE']
    for k,r in inRasters.items():
        if k[6:8].lower()=='lg':
            normData,nd=normalizeRaster(r)
            id = os.path.join(prefix, k) + suffix

            drvr = gdal.GetDriverByName(drvrName)
            outDS = drvr.Create(id, normData.shape[1], normData.shape[0], 1, gdal.GDT_Float32,options=opts)
            outDS.SetGeoTransform(geotrans)
            outDS.SetSpatialRef(spatRef)
            b = outDS.GetRasterBand(1)
            b.SetNoDataValue(nd)
            b.WriteArray(normData)
            normRasters[k]=outDS

    return normRasters


def RasterCopy(id, inDS, drvrName="mem", prefix='', suffix=''):
    """Create a copy of a Raster

    Args:
        id (str): The id of the new index raster.
        inDS (gdal.Dataset): The raster dataset to copy.
        drvrName (str,optional): Name of driver to use to create new raster; defaults to "MEM".
        prefix (str,optional): Prefix to apply to `compName` for gdal.Dataset label; this could be a path to a directory
           if raster is being saved to disk.
        suffix (str,optional): Suffix to apply to `compName` for gdal.Dataset label; this could be the file extension
           if raster is being saved to disk.

    Returns:
        gdal.Dataset: The copy of the dataset.
    """
    path = os.path.join(prefix, id) + suffix
    drvr = gdal.GetDriverByName(drvrName)

    ds = drvr.CreateCopy(path, inDS)
    return ds


def RasterDistance(id, inDS, drvrName="mem", prefix='', suffix='', mask=None, distThresh=None, gdType=gdal.GDT_Float32,opts=None):
    """Compute distances for values in raster.

    Args:
        id (str): The id for the newly created Raster.
        inDS (gdal.Dataset): The Raster to calculate distances for.
        drvrName (str,optional): Name of driver to use to create new raster; defaults to "MEM".
        prefix (str,optional): Prefix to apply to `compName` for gdal.Dataset label; this could be a path to a directory
           if raster is being saved to disk.
        suffix (str,optional): Suffix to apply to `compName` for gdal.Dataset label; this could be the file extension
           if raster is being saved to disk.
        mask (numpy.ndarray,optional): No-data mask to apply to generated distance raster.
        distThresh (Numeric,optional): Optional threshold to apply to distance calculation.
        gdType (int,optional): Flag indicating the data type for the raster; default is "gdal.GDT_Float32".

    Returns:
        gdal.Dataset: The newly generated distance Raster.
    """

    path = os.path.join(prefix, id) + suffix
    drvr = gdal.GetDriverByName(drvrName)
    inOpts=[]
    if opts!=None:
        inOpts=opts
    ds = drvr.Create(path, inDS.RasterXSize, inDS.RasterYSize, 1, gdType,options=inOpts)

    inBand = inDS.GetRasterBand(1)

    ds.SetGeoTransform(inDS.GetGeoTransform())
    ds.SetSpatialRef(inDS.GetSpatialRef())
    outBand = ds.GetRasterBand(1)
    outND = np.inf  # NOTE: don't use NaN here; it complicates later comparisons
    outBand.SetNoDataValue(outND)
    # fill = np.full([inDS.RasterYSize, inDS.RasterXSize], nodata, dtype=gdt_np_map[gdType])
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
    """Normalize the values in a Raster.

    Args:
        inRast (gdal.Dataset): The Raster to normalize.
        flip (bool,optional): If `True` (the default), invert the normalized values; transform every value `n` to
           `1-n`.

    Returns:
        tuple: Returns a numpy.ndarray that represents the normalized raster data, and the value representing no-data.
    """
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


def MultBandData(data1, data2, id, nd1, nd2, geotrans, spatRef, drvrName='mem',opts=None):
    """Multiply two bands of raster datat together.

    Args:
        data1 (numpy.ndarray): The first raster band to multiply.
        data2 (numpy.ndarray): The second raster band to multiply.
        id (str): The id to apply to the new raster.
        nd1 (float): The no-data value for the first raster band.
        nd2 (float): The no-data value for the second raster band.
        geotrans (tuple): Matrix of float values describing geographic transformation.
        spatRef (osr.SpatialReference): The Spatial Reference System to provide for the new Raster.
        drvrName (str,optional): Name of driver to use to create new raster; defaults to "MEM".

    Returns:
        ds.Dataset: The raster representing the product of the two raster bands.
    """

    prod = np.full_like(data1, nd1, dtype=np.float32)
    prod1D = prod.ravel()

    for i, (d1, d2) in enumerate(zip(data1.ravel(), data2.ravel())):
        if d1 != nd1 and d2 != nd2:
            prod1D[i] = d1 * d2

    drvr = gdal.GetDriverByName(drvrName)
    inOpts=[]
    if opts is not None:
        inOpts=opts
    outDS = drvr.Create(id, data1.shape[1], data1.shape[0], 1, gdal.GDT_Float32,options=inOpts)
    outDS.SetGeoTransform(geotrans)
    outDS.SetSpatialRef(spatRef)
    b = outDS.GetRasterBand(1)
    b.SetNoDataValue(nd1)
    b.WriteArray(prod)
    return outDS


def buildPandasDataframe(indexRasters, dataRasters,indexId='lg',indexDFName='LG_index'):
    """Convert a RasterGroup to a pandas DataFrame.

    Args:
        indexRasters (RasterGroup): RasterGroup which contains the index layer specified by `indexId`.
        dataRasters (RasterGroup): The data to convert into a pandas DataFrame.
        indexId (str,optional): The indexRaster to use to map data to rows; defaults to 'lg'.
        indexDFName (str,optional): The name of the index column in the DataFrame; defaults to 'LG_index'.

    Returns:
        pandas.DataFrame: The newly created dataframe.
    """

    lgDS = indexRasters[indexId]
    lgArray=lgDS.GetRasterBand(1).ReadAsArray()
    lgNd = lgDS.GetRasterBand(1).GetNoDataValue()
    columns,hitmap = dataRasters.generateHitMap()

    df = pd.DataFrame(data=None, columns=[indexDFName]+columns)
    df[indexDFName]=lgArray.ravel()
    df.set_index(indexDFName, inplace=True)

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

def DataFrameToRasterGroup(df, indexRaster, cols=None, gdtype=gdal.GDT_Float32):
    """Convert a pandas DataFrame into a series of rasters.

    Args:
        df (pandas.DataFrame): The DataFrame containing the columns to convert.
        indexRaster (gdal.Dataset or str): The raster (or path to raster) to use as the indexing reference, and as a
           template to generated rasters.
        cols (list,optional): A list of columns to Rasterize. If `None` (the default), rasterize all columns.
        gdType (int,optional): Flag indicating the data type for the raster; default is "gdal.GDT_Float32".

    Returns:
        RasterGroup: The newly generated Rasters.
    """

    if isinstance(indexRaster, str):
        indexRaster = gdal.Open(indexRaster)

    if cols is None:
        cols = list(df.columns)
    lgBand = indexRaster.GetRasterBand(1)
    lgNoData = lgBand.GetNoDataValue()
    lgBuff = lgBand.ReadAsArray()
    lgFlat = lgBuff.ravel()
    outRasters = RasterGroup()

    for c in cols:
        slice = df[c]
        outBuff=np.array(lgBuff,dtype=gdt_np_map[gdtype])
        flatBuff=outBuff.ravel()
        for i in range(len(flatBuff)):
            if lgFlat[i]!=lgNoData:
                flatBuff[i]=slice[lgFlat[i]]
        ds=writeRaster(indexRaster, outBuff, c, 'mem', gdtype, nodata=lgNoData)
        outRasters.add(c,ds)
    return outRasters
