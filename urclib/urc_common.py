"""Misc functions and classes used in URC calculations."""

import sys
import fnmatch

from osgeo import gdal
from .common_utils import *
import pandas as pd


class RasterGroup(object):
    """Container for storing Rasters which share the same dimensions and geotransformations.

    Keyword Args:
        kwargs: Any provide named arguments are expected to have a gdal.Dataset as a value, and the key will
          be reused as the reference id.
    """

    def __init__(self, **kwargs):

        self._rasters = {}
        self._cached_ref = None

        not_found = []
        for k, v in kwargs.items():
            try:
                self.add(k, v)
            except RuntimeError:
                not_found.append(v)
        if len(not_found) > 0:
            raise RuntimeError("The following files were not found:" + ",".join(not_found))

    def __contains__(self, item):
        return item in self._rasters

    def __repr__(self):
        return f'Rasters={", ".join(self.raster_names)}'

    def __getitem__(self, item):
        return self._rasters[item]

    def __setitem__(self, key, value):
        self.add(key, value)

    def __delitem__(self, key):
        if self._rasters[key] == self._cached_ref:
            self._cached_ref = None
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
            id (str): The dlg_label to apply to the raster dataset.
            path_or_ds (str or gdal.Dataset): Either a path to a raster, or a loaded raster Dataset.

        Raises:
            KeyError: If a raster with the value `id` already exists in the group.
            ValueError: If there are existing rasters in the collection and the new raster does not match
               the dimensions or geotransformation of the existing rasters.
        """
        if id in self._rasters:
            raise KeyError(f"Raster with {id} exists; explicitly delete before adding")

        if isinstance(path_or_ds, gdal.Dataset):
            ds = path_or_ds
        else:
            ds = gdal.Open(path_or_ds)

        # if existing rasters, check for consistancy
        if not self._check_consistancy(ds):
            raise ValueError(f"The raster '{id}'({path_or_ds}) does not match dimensions of existing entries")
        self._rasters[id] = ds

    def generate_hitmap(self, keys=None):
        """Generate a map of presence/absence of data for each raster in group.

        Args:
            keys (list,optional): A list of rasters to include in hitmap generation. If `None`,
              then include all rasters.

        Returns:
            tuple: A list of keys of the rasters included in the analysis, in the order of their inclusion in the
              hitmap, followed by a 3d array representing the hitmap of all included rasters.
              Dimensions are (raster,y,x).
        """

        ret = np.empty([len(self._rasters), self.raster_y_size, self.raster_x_size], dtype=np.uint8)
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
            for y in range(self.raster_y_size):
                for x in range(self.raster_x_size):
                    ret[i, y, x] = 0 if ndv == b[y, x] else 1
        return keys, ret

    def generate_nodata_mask(self):
        """Generate a noData mask for the combination of all included rasters.

        Returns:
            numpy.ndarray: 2D array of an included raster dimension, denoting which cells are valid (1) or nodata (0).
        """
        mask = np.empty([self.raster_y_size, self.raster_x_size], dtype=np.uint8)
        _, hits = self.generate_hitmap()

        for j in range(self.raster_y_size):
            for k in range(self.raster_x_size):
                mask[j, k] = 1 if any(hits[:, j, k] == 1) else 0
        return mask

    def copy_rasters(self, driver, path, suffix='',opts=None):
        """Copy all the rasters in this group using the provided information.

        Args:
            driver (str or gdal.Driver): Either the name of the driver to use for copying, or the Driver object itself.
            path (str): Path to parent directory to write out each raster; acts as dlg_label with drivers that don't
               require paths (such as "MEM").
            suffix (str,optional): The tail to apply to the filepath; typically this is a file extension. Can be
                omitted.
            opts (list,optional): Optional list of strings to pass to the file driver during file creation.

        Returns:
            list: List of newly created gdal.Datasets. This return value can be ignored if just concerned with
              performing a write-only operation.
        """
        if isinstance(driver, str):
            driver = gdal.GetDriverByName(driver)
        if opts is None:
            opts =[]
        copies = []
        for id, ds in self._rasters.items():
            fullpath = os.path.join(path, id + suffix)
            copies.append(driver.CreateCopy(fullpath, ds,options=opts))

        return copies

    def update(self, other):
        """Add content from another RasterGroup. This effectively calls add()
        on all contents of `other`.

        Args:
            other (RasterGroup): The other raster to extract values from.

        Raises:
            ValueError: If `other` is not of type `RasterGroup`.
        """
        if not isinstance(other, RasterGroup):
            raise ValueError("'other' must be of type RasterGroup")
        for k, r in other.items():
            self.add(k, r)

    def clip_with_raster(self, clip_raster, shrink_to_fit=False):
        """Clip all rasters in group using another raster.

        Args:
            clip_raster (gdal.Dataset): The raster to use in clipping operation.
            shrink_to_fit (bool,optional): Presently unused.

        """

        if not self._check_consistancy(clip_raster):
            raise ValueError("Clipping raster must match dimensions of RasterGroup")

        clipband = clip_raster.GetRasterBand(1).ReadAsArray()
        clipflat = clipband.ravel()
        # for each raster, keep mask where 1, else mark as nodata
        for v in self._rasters.values():
            b = v.GetRasterBand(1).ReadAsArray()
            nd = v.GetRasterBand(1).GetNoDataValue()
            bflat = b.ravel()

            for i in range(len(clipflat)):
                if clipflat[i] == 0:
                    bflat[i] = nd
            v.GetRasterBand(1).WriteArray(b)

        # TODO: Shrink to fit is disabled because gdal.Translate does not appear
        # to subwindow properly. Come up with another scheme (maybe warp?)

        # if shrink_to_fit:
        #     # if shrink to fit:
        #
        #     # grab group mask
        #     ndMask=self.generate_nodata_mask()
        #     # find all exts
        #     oX = 0
        #     oY = 0
        #     w = self.raster_y_size
        #     h = self.raster_x_size
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
        #     if any((oX > 0, oY >0,w<self.raster_x_size,h<self.raster_y_size)):
        #         for k in list(self._rasters.keys()):
        #             self._rasters[k] = gdal.Translate(k,self._rasters[k],srcWin=[oX,oY,w,h])

    def calc_max_values(self, prefix=None, out_nodata=-9999):
        """Find the max value for each pixel location across all rasters.

        Args:
            prefix (str,optional): Only include rasters whose keys begin with this. If `None` (default), include all
                rasters in calculation.
            out_nodata (int): The value to use to represent nodata.

        Returns:
            numpy.ndarray: A 2d array of max values, with nodata values marked with the value provided by `outNoData`.
        """
        vals = []
        for k, v in self._rasters.items():
            if prefix is not None and not k.startswith(prefix):
                continue

            b = v.GetRasterBand(1).ReadAsArray()
            nd = v.GetRasterBand(1).GetNoDataValue()
            b[b == nd] = -np.inf
            vals.append(b)

        if len(vals) == 0:
            return None
        ret = np.stack(vals).max(axis=0)
        ret[ret == -np.inf] = out_nodata

        return ret

    def _check_consistancy(self, ds):
        """..."""
        if len(self._rasters) > 0:
            test = self._rasters[tuple(self._rasters.keys())[0]]
            ds_gtf = ds.GetGeoTransform()
            test_gtf = test.GetGeoTransform()
            if ds.RasterXSize != test.RasterXSize or ds.RasterYSize != test.RasterYSize \
                    or any([ds_gtf[i] != test_gtf[i] for i in range(6)]):
                return False
        return True

    def _get_test_raster(self):
        """Retrieve a raster to use for testing for conformance.

        Returns:
            gdal.Dataset: raster to use for testing, or `None` if RasterGroup is empty.
        """
        if self._cached_ref is None:
            if len(self._rasters) != 0:
                self._cached_ref = self._rasters[tuple(self._rasters.keys())[0]]
        return self._cached_ref

    @property
    def raster_names(self):
        """list: Alphabetically sorted list of raster ids/names."""
        return sorted(list(self._rasters.keys()))

    @property
    def extents(self):
        """tuple: The shared real-world extents in (x-min,x-max,y-min,y-max) order."""
        ds = self._get_test_raster()
        if ds is None:
            return (0.,) * 4
        gtf = ds.GetGeoTransform()
        return (gtf[0], gtf[0] + (gtf[1] * ds.RasterXSize),
                gtf[3], gtf[3] + (gtf[5] * ds.RasterYSize))

    @property
    def geotransform(self):
        """tuple: The shared geotransformation matrix for all included rasters."""
        ds = self._get_test_raster()
        if ds is None:
            return (0.,) * 6
        gtf = ds.GetGeoTransform()
        return gtf

    @property
    def spatialref(self):
        """osr.SpatialReference: The spatial reference used by the internal test raster, or `None` if group is empty."""
        ds = self._get_test_raster()
        if ds is None:
            return None
        return ds.GetSpatialRef()

    @property
    def raster_x_size(self):
        """int: The width (in pixels) of all included rasters."""
        ds = self._get_test_raster()
        if ds is None:
            return 0
        return ds.RasterXSize

    @property
    def raster_y_size(self):
        """int: The height (in pixels) of all included rasters."""
        ds = self._get_test_raster()
        if ds is None:
            return 0
        return ds.RasterYSize

    @property
    def empty_raster_names(self):
        """list: Rasters in group which contain only nodata."""
        names = []

        for id, ds in self._rasters.items():
            b = ds.GetRasterBand(1)
            nd = b.GetNoDataValue()
            hit = False
            for v in b.ReadAsArray().ravel():
                if v != nd:
                    hit = True
                    break
            if not hit:
                # if we get here, raster is empty
                names.append(id)

        return names


def list_featureclass_names(ds, wildcard, first_char=0, last_char=sys.maxsize):
    """Function that creates a list of all unique REE-Coal components in an ESRI GDB Feature Dataset, for use in use in
        calculating PE score from DA and DS databases.

    Args:
        ds (osgeo.gdal.Dataset): The dataset to query.
        wildcard (str): Criteria used to limit the results returned.
        first_char (int,optional): Index of first character to include in the filename.
            Defaults to 0.
        last_char (int,optional): Index of lastcharacter to include in the filename.
            Defaults to position of last character in string.

    Returns:
        list: sorted, non-repeating iterable sequence of layer names based on the WildCard criteria
    """

    fc_names = [ds.GetLayer(i).GetName() for i in range(ds.GetLayerCount())]
    # match against wildcard
    fc_names = [x[first_char:last_char] for x in fnmatch.filter(fc_names, wildcard)]

    return sorted(set(fc_names))


def list_featureclasses(ds, wildcard):
    """Function that creates a list of all unique REE-Coal components in an ESRI GDB Feature Dataset, for use in use in
        calculating PE score from DA and DS databases.

    Args:
        ds (osgeo.gdal.Dataset): The dataset to query.
        wildcard (str): Criteria used to limit the results returned.

    Returns:
        list: sorted, non-repeating iterable sequence of Layers based on the WildCard criteria
    """

    fc_names = list_featureclass_names(ds, wildcard)

    fc_list = []
    for i in range(ds.GetLayerCount()):
        lyr = ds.GetLayer(i)
        if lyr.GetName() in fc_names:
            fc_list.append(lyr)

    return fc_list


def find_unique_components(gdb_ds, prefix):
    """Find the collections to be used in subsequent steps.

    Args:
        gdb_ds (osgeo.gdal.Dataset): Dataset containing features to parse. Expected to
          originate from a file geodatabase (.gdb) file.
        prefix (str): The prefix used to filter returned layers.

    Returns:
        tuple:
            0. list: List of unique layer names.
            1. list: Layer objects corresponding to labels in entry 0.
    """

    # Create a list of all unique code prefixes for the component IDs
    unique_components = list_featureclass_names(gdb_ds, wildcard=prefix + "*", first_char=0, last_char=14)

    # An array comprising all components and their respective feature classes
    components_data = {}

    # Generate a list of feature classes for each Emplacement Type, Influence Extent, AND Component ID combination
    for uc in unique_components:
        component_datasets = list_featureclasses(gdb_ds, wildcard=(uc + "*"))

        # Append list to a single array
        components_data[uc] = component_datasets

    return components_data


def rasterize_components(src_rasters, gdb_ds, component_data, cache_dir=None, mask=None):
    """Convert specified vector layers into raster datasets.

    Args:
        src_rasters (RasterGroup): The RasterGroup container to use as frame of reference for conversion.
        gdb_ds (gdal.Dataset): Source of vector layers to convert.
        component_data (dict): Id and vector components to Raster.
        cache_dir (str,optional): If present, save generated rasters to the specified folder.
        mask (numpy.ndarray,optional): If present, apply mask to newly created rasters.

    Returns:
        RasterGroup: collection of newly rasterized components.
    """

    src_data = {'xsize': src_rasters.raster_x_size,
                'ysize': src_rasters.raster_y_size,
                'geotrans': src_rasters.geotransform,
                'srs': src_rasters.spatialref,
                'nodata': 0,
                'gdtype': gdal.GDT_Byte,
                'drvr_name': 'mem',
                'prefix': '',
                'suffix': '',
                }

    if cache_dir is not None:
        src_data['drvr_name'] = 'GTiff'
        src_data['prefix'] = cache_dir
        src_data['suffix'] = '.tif'
        src_data['opts'] = GEOTIFF_OPTIONS

    out_rasters = RasterGroup()
    for id, fc_list in component_data.items():
        print(f'Rasterizing {id}...')
        rstr = rasterize(id, fc_list, gdb_ds, **src_data)
        out_rasters[id] = rstr
        if mask is not None:
            b = rstr.GetRasterBand(1)
            raw = b.ReadAsArray()
            raw[mask == 0] = src_data['nodata']
            b.WriteArray(raw)

    return out_rasters


def gen_domain_hitmaps(src_rasters):
    """Generate hitmaps for each domain component.

    Args:
        src_rasters (RasterGroup): The index rasters to use for generating the hitmaps.

    Returns:
        dict: Collection of index hitmaps for ld, ud, and sd domains, along with which values were hit.
    """

    hitmaps = {}
    search_doms = ['ld', 'ud', 'sd']
    if 'sa' in src_rasters:
        search_doms.append('sa')

    for k in search_doms:
        print(f'Separating {k} domains...')
        srcband = src_rasters[k].GetRasterBand(1)
        _, maxval = srcband.ComputeRasterMinMax(0)
        maxval = int(maxval)
        ndval = srcband.GetNoDataValue()
        hitlist = [False] * (maxval + 1)
        # separate values out for individual domains
        sub_buffs = np.zeros([maxval + 1, src_rasters.raster_y_size, src_rasters.raster_x_size], dtype=np.uint8)
        src_buff = srcband.ReadAsArray()
        for i in range(src_rasters.raster_y_size):
            for j in range(src_rasters.raster_x_size):
                px = src_buff[i, j]
                if px != ndval:
                    sub_buffs[px, i, j] = 1
                    hitlist[px] = True

        # cache hitmaps
        hitmaps[k] = (sub_buffs, hitlist)
    return hitmaps


def gen_domain_index_rasters(src_rasters, as_distance, cache_dir=None, mask=None):
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
        'drvr_name': 'mem',
        'prefix': '',
        'suffix': '',
    }
    if as_distance:
        src_data['mask'] = mask
        src_data['gdtype']: gdal.GDT_Float32
    if cache_dir is not None:
        src_data['drvr_name'] = 'GTiff'
        src_data['prefix'] = cache_dir
        src_data['suffix'] = '.tif'
        src_data['opts'] = GEOTIFF_OPTIONS

    hitmaps = gen_domain_hitmaps(src_rasters)

    out_rasters = RasterGroup()

    # scratch buffer
    drvr = gdal.GetDriverByName("mem")
    scratch_ds = drvr.Create("scratch", src_rasters.raster_x_size, src_rasters.raster_y_size, 1, gdal.GDT_Int32)
    scratch_ds.SetGeoTransform(src_rasters.geotransform)
    scratch_ds.SetSpatialRef(src_rasters.spatialref)
    scratch_band = scratch_ds.GetRasterBand(1)
    scratch_band.SetNoDataValue(0)

    for k, (subBuffs, hitList) in hitmaps.items():

        print(f'{"Distancing for" if as_distance else "Isolating"} {k} domains...')
        # cache hitmaps
        hitmaps[k] = subBuffs

        # build distances for each domain
        for i in range(subBuffs.shape[0]):
            if not hitList[i]:
                continue
            scratch_band.WriteArray(subBuffs[i])
            id = f'{k}_{i}'

            if as_distance:
                rstr = raster_distance(id, scratch_ds, **src_data)
            else:
                rstr = raster_copy(id, scratch_ds, **src_data)
            out_rasters[id] = rstr

    return out_rasters, hitmaps


def find_domain_component_rasters(dom_dist_rasters, hit_maps, test_rasters, cache_dir=None):
    """Find Domain/index overlap for individual components.

    Args:
        dom_dist_rasters (RasterGroup): Rasters containing domain distances.
        hit_maps (dict): key is name of raster in `test_rasters`, value is numpy.ndarray as hit map for associated
            index.
        test_rasters (RasterGroup): The domain indices rasters to use for domain expansion.
        cache_dir (str,optional): If present, save generated rasters to the specified folder.

    Returns:
        RasterGroup: The newly created domain-component distance rasters.
    """

    combo_rasters = RasterGroup()
    fixed_args = {
        'drvr_name': 'mem',
        'prefix': '',
        'suffix': '',
        'combo_rasters': combo_rasters,
        'domdist_rasters': dom_dist_rasters,
    }

    if cache_dir is not None:
        fixed_args['drvr_name'] = 'GTiff'
        fixed_args['prefix'] = cache_dir
        fixed_args['suffix'] = '_domain_component.tif'
        fixed_args['opts']=GEOTIFF_OPTIONS

    for id, srcDS in test_rasters.items():
        dom_key = id[6:8].lower()
        if dom_key not in hit_maps:
            continue
        test_band = srcDS.GetRasterBand(1)
        test_buff = test_band.ReadAsArray()
        nd = test_band.GetNoDataValue()
        hm = hit_maps[dom_key]
        found = set()  # {x for x in testBand.ReadAsArray().ravel() if x!=nd}
        for i in range(dom_dist_rasters.raster_y_size):
            for j in range(dom_dist_rasters.raster_x_size):
                v = test_buff[i, j]
                if v != nd and v != 0:
                    for h in range(hm.shape[0]):
                        if hm[h, i, j] != 0:
                            found.add(h)
        combine_domdist_rasters(found, dom_key, id, **fixed_args)
    return combo_rasters


def combine_domdist_rasters(found, domkey, comp_name, domdist_rasters, combo_rasters, prefix='', suffix='',
                            drvr_name='mem',opts=None):
    """Combine individual domain indices rasters into new raster.

    Args:
        found (set): Collection of domain indices triggered in hitmap.
        domkey (str): The domain key (ie 'ld','ud',or 'sd').
        comp_name (str): Label or path to apply to newly created raster
        domdist_rasters (RasterGroup): Collection of domain distance rasters.
        combo_rasters (RasterGroup): The collection to add the newly generated raster to.
        prefix (str,optional): Prefix to apply to `comp_name` for gdal.Dataset dlg_label; this could be a path to a
            directory if raster is being saved to disk.
        suffix (str,optional): Suffix to apply to `comp_name` for gdal.Dataset dlg_label; this could be the file extension
           if raster is being saved to disk.
        drvr_name (str,optional): Name of driver to use to create new raster; defaults to "MEM".
        opts (list,optional): String flags to forward to GDAL drivers, if any.

    """

    path = os.path.join(prefix, comp_name) + suffix
    out_nd = np.inf
    out_buff = np.full([domdist_rasters.raster_y_size, domdist_rasters.raster_x_size], out_nd, dtype=np.float32)
    for index in found:
        ds = domdist_rasters[f'{domkey}_{index}']
        b = ds.GetRasterBand(1)
        in_nd = b.GetNoDataValue()
        read_buff = b.ReadAsArray()
        for i in range(ds.RasterYSize):
            for j in range(ds.RasterXSize):
                if read_buff[i, j] == in_nd:
                    continue
                if out_buff[i, j] == out_nd or out_buff[i, j] > read_buff[i, j]:
                    out_buff[i, j] = read_buff[i, j]

    drvr = gdal.GetDriverByName(drvr_name)
    print("Combine: writing " + path)

    if opts is None:
        opts = []
    out_ds = drvr.Create(path, domdist_rasters.raster_x_size, domdist_rasters.raster_y_size, 1, gdal.GDT_Float32,
                         options=opts)
    out_ds.SetGeoTransform(domdist_rasters.geotransform)
    out_ds.SetSpatialRef(domdist_rasters.spatialref)
    out_band = out_ds.GetRasterBand(1)
    out_band.SetNoDataValue(out_nd)
    out_band.WriteArray(out_buff)
    combo_rasters.add(comp_name, out_ds)


def norm_multrasters(implicits, explicits, cache_dir=None):
    """Normalize and multiply rasters; match using input raster names.

    Args:
        implicits (RasterGroup): Rasters containing implicit data.
        explicits (RasterGroup): Rasters containing explicit data.
        cache_dir (str,optional): If present, save generated rasters to the specified folder.

    Returns:
        RasterGroup: The products of normalization and multiplication.
    """

    multrasters = RasterGroup()

    kwargs = {'geotrans': implicits.geotransform,
              'spatref': implicits.spatialref,
              'drvr_name': 'mem'
              }

    prefix = ''
    suffix = ''
    if cache_dir is not None:
        kwargs['drvr_name'] = 'GTiff'
        kwargs['opts'] = GEOTIFF_OPTIONS
        prefix = cache_dir
        suffix = '_norm_product.tif'

    for k in implicits.raster_names:
        imp = implicits[k]
        exp = explicits[k]

        norm_imp, imp_nd = normalize_raster(imp)
        norm_exp, exp_nd = normalize_raster(exp)

        id = os.path.join(prefix, k) + suffix
        multrasters[k] = mult_band_data(norm_imp, norm_exp, id, imp_nd, exp_nd, **kwargs)

    return multrasters


def norm_lg_rasters(in_rasters, cache_dir=None):
    """Normalize LG rasters.

    Args:
        in_rasters (RasterGroup): The rasters to be transformed.
        cache_dir (str,optional): A directory to write the normalized rasters to. If `None`, keep rasters in memory
             only.

    Returns:
        RasterGroup: The normalized contents of `in_rasters`.
    """

    norm_rasters = RasterGroup()

    geotrans = in_rasters.geotransform
    spat_ref = in_rasters.spatialref
    drvr_name = 'mem'
    prefix = ''
    suffix = ''
    opts = []
    if cache_dir is not None:
        drvr_name = 'GTiff'
        prefix = cache_dir
        suffix = '_norm_distance.tif'
        opts = GEOTIFF_OPTIONS
    for k, r in in_rasters.items():
        if k[6:8].lower() == 'lg':
            norm_data, nd = normalize_raster(r)
            id = os.path.join(prefix, k) + suffix

            drvr = gdal.GetDriverByName(drvr_name)
            out_ds = drvr.Create(id, norm_data.shape[1], norm_data.shape[0], 1, gdal.GDT_Float32, options=opts)
            out_ds.SetGeoTransform(geotrans)
            out_ds.SetSpatialRef(spat_ref)
            b = out_ds.GetRasterBand(1)
            b.SetNoDataValue(nd)
            b.WriteArray(norm_data)
            norm_rasters[k] = out_ds

    return norm_rasters


def raster_copy(id, in_ds, drvr_name="mem", prefix='', suffix='',opts=None):
    """Create a copy of a Raster

    Args:
        id (str): The id of the new index raster.
        in_ds (gdal.Dataset): The raster dataset to copy.
        drvr_name (str,optional): Name of driver to use to create new raster; defaults to "MEM".
        prefix (str,optional): Prefix to apply to `comp_name` for gdal.Dataset dlg_label; this could be a path to a
            directory if raster is being saved to disk.
        suffix (str,optional): Suffix to apply to `comp_name` for gdal.Dataset dlg_label; this could be the file extension
           if raster is being saved to disk.
        opts (list,optional): Optional list of strings to pass to the file driver during file creation.

    Returns:
        gdal.Dataset: The copy of the dataset.
    """
    path = os.path.join(prefix, id) + suffix
    drvr = gdal.GetDriverByName(drvr_name)

    ds = drvr.CreateCopy(path, in_ds,options=opts)
    return ds


def raster_distance(id, in_ds, drvr_name="mem", prefix='', suffix='', mask=None, dist_thresh=None,
                    gdtype=gdal.GDT_Float32, opts=None):
    """Compute distances for values in raster.

    Args:
        id (str): The id for the newly created Raster.
        in_ds (gdal.Dataset): The Raster to calculate distances for.
        drvr_name (str,optional): Name of driver to use to create new raster; defaults to "MEM".
        prefix (str,optional): Prefix to apply to `comp_name` for gdal.Dataset dlg_label; this could be a path to a
            directory if raster is being saved to disk.
        suffix (str,optional): Suffix to apply to `comp_name` for gdal.Dataset dlg_label; this could be the file extension
           if raster is being saved to disk.
        mask (numpy.ndarray,optional): No-data mask to apply to generated distance raster.
        dist_thresh (Numeric,optional): Optional threshold to apply to distance calculation.
        gdtype (int,optional): Flag indicating the data type for the raster; default is "gdal.GDT_Float32".
        opts (list,optional): Optional list of strings to pass to the file driver during file creation.

    Returns:
        gdal.Dataset: The newly generated distance Raster.
    """

    path = os.path.join(prefix, id) + suffix
    drvr = gdal.GetDriverByName(drvr_name)
    in_opts = []
    if opts is not None:
        in_opts = opts
    ds = drvr.Create(path, in_ds.RasterXSize, in_ds.RasterYSize, 1, gdtype, options=in_opts)

    inband = in_ds.GetRasterBand(1)

    ds.SetGeoTransform(in_ds.GetGeoTransform())
    ds.SetSpatialRef(in_ds.GetSpatialRef())
    outband = ds.GetRasterBand(1)
    out_nd = np.inf  # NOTE: don't use NaN here; it complicates later comparisons
    outband.SetNoDataValue(out_nd)
    # fill = np.full([in_ds.raster_y_size, in_ds.raster_x_size], nodata, dtype=gdt_np_map[gdtype])
    # outBand.WriteArray(fill)

    argstr = "DISTUNITS=GEO"
    if dist_thresh is not None:
        argstr += f" MAXDIST={dist_thresh}"
    gdal.ComputeProximity(inband, outband, [argstr])

    # do some corrections
    buffer = outband.ReadAsArray()
    rbuff = buffer.ravel()
    # replace nodatas with 0 distance
    rbuff[rbuff == out_nd] = 0

    # apply mask if provided
    if mask is not None:
        buffer[mask == 0] = out_nd

    outband.WriteArray(buffer)
    return ds


def normalize_raster(in_rast, flip=True):
    """Normalize the values in a Raster.

    Args:
        in_rast (gdal.Dataset): The Raster to normalize.
        flip (bool,optional): If `True` (the default), invert the normalized values; transform every value `n` to
           `1-n`.

    Returns:
        tuple: Returns a numpy.ndarray that represents the normalized raster data, and the value representing no-data.
    """
    band = in_rast.GetRasterBand(1)
    ndval = band.GetNoDataValue()
    raw = band.ReadAsArray()
    out = np.full_like(raw, ndval, dtype=raw.dtype)

    # grab 1d views to simplify parsing
    raw1d = raw.ravel()
    out1d = out.ravel()

    # cant use gdal.band.ComputeRasterMinMax(),since it breaks if raster is empty
    min_val = np.inf
    max_val = -np.inf
    for i in range(len(raw1d)):
        if raw1d[i] != ndval:
            min_val = min(min_val, raw1d[i])
            max_val = max(max_val, raw1d[i])
    ext = max_val - min_val

    if max_val != -np.inf or min_val != np.inf:

        for i in range(len(raw1d)):
            if raw1d[i] != ndval:
                if ext != 0.:
                    out1d[i] = (raw1d[i] - min_val) / ext
                else:
                    # in the case were there is only a singular value,
                    # assume that distance is 0
                    out1d[i] = 0

                if flip:
                    out1d[i] = 1 - out1d[i]
    else:
        out = raw
    return out, ndval


def mult_band_data(data1, data2, id, nd1, nd2, geotrans, spatref, drvr_name='mem', opts=None):
    """Multiply two bands of raster datat together.

    Args:
        data1 (numpy.ndarray): The first raster band to multiply.
        data2 (numpy.ndarray): The second raster band to multiply.
        id (str): The id to apply to the new raster.
        nd1 (float): The no-data value for the first raster band.
        nd2 (float): The no-data value for the second raster band.
        geotrans (tuple): Matrix of float values describing geographic transformation.
        spatref (osr.SpatialReference): The Spatial Reference System to provide for the new Raster.
        drvr_name (str,optional): Name of driver to use to create new raster; defaults to "MEM".
        opts (list,optional): Optional list of strings to pass to the file driver during file creation.

    Returns:
        ds.Dataset: The raster representing the product of the two raster bands.
    """

    prod = np.full_like(data1, nd1, dtype=np.float32)
    prod_1d = prod.ravel()

    for i, (d1, d2) in enumerate(zip(data1.ravel(), data2.ravel())):
        if d1 != nd1 and d2 != nd2:
            prod_1d[i] = d1 * d2

    drvr = gdal.GetDriverByName(drvr_name)
    in_opts = []
    if opts is not None:
        in_opts = opts
    out_ds = drvr.Create(id, data1.shape[1], data1.shape[0], 1, gdal.GDT_Float32,
                         options=in_opts)
    out_ds.SetGeoTransform(geotrans)
    out_ds.SetSpatialRef(spatref)
    b = out_ds.GetRasterBand(1)
    b.SetNoDataValue(nd1)
    b.WriteArray(prod)
    return out_ds


def build_pandas_dataframe(index_rasters, data_rasters, index_id='lg', index_df_name='LG_index'):
    """Convert a RasterGroup to a pandas DataFrame.

    Args:
        index_rasters (RasterGroup): RasterGroup which contains the index layer specified by `index_id`.
        data_rasters (RasterGroup): The data to convert into a pandas DataFrame.
        index_id (str,optional): The index_raster to use to map data to rows; defaults to 'lg'.
        index_df_name (str,optional): The name of the index column in the DataFrame; defaults to 'LG_index'.

    Returns:
        pandas.DataFrame: The newly created dataframe.
    """

    lg_ds = index_rasters[index_id]
    lg_array = lg_ds.GetRasterBand(1).ReadAsArray()
    lg_nd = lg_ds.GetRasterBand(1).GetNoDataValue()
    columns, hitmap = data_rasters.generate_hitmap()

    df = pd.DataFrame(data=None, columns=[index_df_name] + columns)
    df[index_df_name] = lg_array.ravel()
    df.set_index(index_df_name, inplace=True)

    # hitmap dimensions are (rasters,y,x)
    # column = rasters
    # LG/row = y*raster_x_size + x
    # reshape to make parsing easier; this should preserve index ordering
    hitmap_1d = hitmap.reshape([hitmap.shape[0], hitmap.shape[1] * hitmap.shape[2]])
    for i, lbl in enumerate(columns):
        df[lbl] = hitmap_1d[i]

    # drop noData cells
    df.drop(index=lg_nd, inplace=True)
    return df


def dataframe_to_rastergroup(df, index_raster, cols=None, gdtype=gdal.GDT_Float32):
    """Convert a pandas DataFrame into a series of rasters.

    Args:
        df (pandas.DataFrame): The DataFrame containing the columns to convert.
        index_raster (gdal.Dataset or str): The raster (or path to raster) to use as the indexing reference, and as a
           template to generated rasters.
        cols (list,optional): A list of columns to rasterize. If `None` (the default), rasterize all columns.
        gdtype (int,optional): Flag indicating the data type for the raster; default is "gdal.GDT_Float32".

    Returns:
        RasterGroup: The newly generated Rasters.
    """

    if isinstance(index_raster, str):
        index_raster = gdal.Open(index_raster)

    if cols is None:
        cols = list(df.columns)
    lg_band = index_raster.GetRasterBand(1)
    lg_nodata = lg_band.GetNoDataValue()
    lg_buff = lg_band.ReadAsArray()
    lg_flat = lg_buff.ravel()
    out_rasters = RasterGroup()

    for c in cols:
        slice = df[c]
        out_buff = np.array(lg_buff, dtype=gdt_np_map[gdtype])
        flat_buff = out_buff.ravel()
        for i in range(len(flat_buff)):
            if lg_flat[i] != lg_nodata:
                flat_buff[i] = slice[lg_flat[i]]
        ds = write_raster(index_raster, out_buff, c, 'mem', gdtype, nodata=lg_nodata)
        out_rasters.add(c, ds)
    return out_rasters
