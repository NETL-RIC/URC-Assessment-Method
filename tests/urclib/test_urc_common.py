# This file is part of URC Assessment Method.
#
# URC Assessment Method is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# URC Assessment Method is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with URC Assessment Method. If not, see
# <https://www.gnu.org/licenses/>.

import pytest

from urclib.urc_common import *

_EPSG_CODE = 3857 # WGS 84 / pseudo-mercator
_DEFAULT_SHAPE = [30,20]

def _generate_raster(path,data,drvrName,gdtype,nodata):
    drvr = gdal.GetDriverByName(drvrName)
    opts=[]
    if drvrName.lower()=='gtiff':
        opts=GEOTIFF_OPTIONS
    ds = drvr.Create(path,data.shape[1],data.shape[0],1,gdtype,options=opts)

    prj = osr.SpatialReference()
    prj.ImportFromEPSG(_EPSG_CODE)
    ds.SetSpatialRef(prj)
    # skip projection, geotrans
    b = ds.GetRasterBand(1)
    b.SetNoDataValue(nodata)
    b.WriteArray(data)

    return ds

def _generate_tif_raster(path,data,nodata=-9999.):
    return _generate_raster(path,data,'gtiff',gdal.GDT_Float32,nodata)

def _generate_mem_raster(data,nodata=-9999.):
    return _generate_raster('mem',data,'MEM',gdal.GDT_Float32,nodata)

@pytest.fixture(scope="session")
def geos_scratch(tmp_path_factory):
    return tmp_path_factory.mktemp('geoScratch')

@pytest.fixture(scope="session")
def dummy_rasters(geos_scratch):

    rDir = geos_scratch

    paths = [os.path.join(rDir,n) for n in ('testRast1.tif','testRast2.tif','testRastDiff.tif','testClip.tif')]
    nodata=-9999.
    data = np.full(_DEFAULT_SHAPE,nodata,dtype=np.float32)
    # add strip of data
    data[5,...]=[i/_DEFAULT_SHAPE[1] for i in range(_DEFAULT_SHAPE[1])]
    _generate_tif_raster(paths[0],data,nodata=nodata)
    data = np.full(_DEFAULT_SHAPE, nodata, dtype=np.float32)
    # add strip of data
    data[..., 11] = [i + _DEFAULT_SHAPE[0] for i in range(_DEFAULT_SHAPE[0])]
    _generate_tif_raster(paths[1], data, nodata=nodata)

    # different sized raster
    data = np.ones([50, 20], dtype=np.float32)
    _generate_tif_raster(paths[2], data, nodata=nodata)

    return paths

@pytest.fixture(scope="session")
def dummy_vectors(geos_scratch):
    vDir = geos_scratch
    paths = [os.path.join(vDir,p) for p in ('dummydata.sqlite',)]

    drvr = gdal.GetDriverByName('SQLite')
    ds = drvr.Create(paths[0],0,0,0,gdal.OF_VECTOR)
    ds.CreateLayer('DA_1')
    ds.CreateLayer('DA_2')
    ds.CreateLayer('DS_1')

    return paths

@pytest.fixture(scope="function")
def dummy_rastergroup(dummy_rasters):
    return RasterGroup(test1=dummy_rasters[0],test2=dummy_rasters[1])

@pytest.fixture(scope="function")
def raster_copy_scratch(tmp_path_factory):
    return tmp_path_factory.mktemp('raster_copies')

class TestRasterGroup(object):

    def test_default_construct(self):
        grp = RasterGroup()
        assert len(grp) == 0

    def test_keyword_construct(self,dummy_rasters):
        grp = RasterGroup(t1=dummy_rasters[0],t2=dummy_rasters[1])
        # grp=dummy_rastergroup
        assert len(grp)==2

        with pytest.raises(RuntimeError):
            grp=RasterGroup(missing='not/present')

    def test___contains__(self,dummy_rastergroup):
        assert 'test1' in dummy_rastergroup
        assert 'missing' not in dummy_rastergroup

    def test___repr__(self,dummy_rastergroup):

        repr = dummy_rastergroup.__repr__()
        trg='Rasters='+', '.join(dummy_rastergroup.raster_names)
        assert repr==trg

    def test___getitem__(self,dummy_rastergroup,dummy_rasters):
        ds = dummy_rastergroup['test1']
        assert ds.GetFileList()[0] == dummy_rasters[0]
        with pytest.raises(KeyError):
            ds = dummy_rastergroup['badtag']

    def test___delitem__(self,dummy_rastergroup):

        count = len(dummy_rastergroup)
        del dummy_rastergroup['test1']
        assert len(dummy_rastergroup)==count-1

        # ensure _cached_ref is cleared
        # trigger _cached_ref creation
        dummy_rastergroup.extents
        del dummy_rastergroup['test2']
        assert len(dummy_rastergroup)==0

    def test_add(self,dummy_rasters):

        grp=RasterGroup()
        # add by path
        grp.add('test1',dummy_rasters[0])
        # add by ds
        ds = gdal.OpenEx(dummy_rasters[1])
        grp.add('test2',ds)

        # try to add existing key
        with pytest.raises(KeyError):
            grp.add('test1','')

        # try to add raster with different size
        with pytest.raises(ValueError):
            grp.add('test3',dummy_rasters[2])

    def test_generate_hitmap(self,dummy_rastergroup):

        hit,hitmap = dummy_rastergroup.generate_hitmap()
        assert len(hit)==len(dummy_rastergroup)
        assert isinstance(hitmap,np.ndarray)

        # test key specific
        hit, hitmap = dummy_rastergroup.generate_hitmap(keys=['test1'])
        assert len(hit) == 1
        assert isinstance(hitmap, np.ndarray)

    def test_generate_nodata_mask(self,dummy_rastergroup):

        ndMask = dummy_rastergroup.generate_nodata_mask()
        assert ndMask.shape[1] == dummy_rastergroup.raster_x_size
        assert ndMask.shape[0] == dummy_rastergroup.raster_y_size

    def test_copy_rasters(self,dummy_rastergroup,raster_copy_scratch):

        copies=dummy_rastergroup.copy_rasters('GTiff',raster_copy_scratch,suffix='.tif',opts=GEOTIFF_OPTIONS)

        assert len(copies)==len(dummy_rastergroup)
        for n,_ in dummy_rastergroup.items():
            assert os.path.exists(os.path.join(raster_copy_scratch,f'{n}.tif'))

    def test_update(self,dummy_rastergroup):
        newGrp = RasterGroup()
        # test with other raster group
        newGrp.update(dummy_rastergroup)
        assert all([k in list(dummy_rastergroup.keys()) for k in newGrp.keys()])

        # test with non-raster group
        with pytest.raises(ValueError):
            newGrp.update({})

    def test_clip_with_raster(self,dummy_rastergroup):

        # build clip
        data = np.ones([dummy_rastergroup.raster_y_size,dummy_rastergroup.raster_x_size],dtype=np.float32)
        for y in range(data.shape[0]):
            for x in range(data.shape[1]):
                if y==0 or y== data.shape[0]-1 or x==0 or x== data.shape[1]-1:
                    data[y,x]=0.

        ds=_generate_mem_raster(data)

        drvr = gdal.GetDriverByName('MEM')
        # create copies of rasters, add to new RasterGroup
        copies = dummy_rastergroup.copy_rasters(drvr, 'scratch')
        grp=RasterGroup(t1=copies[0],t2=copies[1])
        grp.clip_with_raster(ds)

        # verify
        for r in grp.values():
            b = r.GetRasterBand(1)
            data=b.ReadAsArray()
            nd=b.GetNoDataValue()
            for y in range(data.shape[0]):
                for x in range(data.shape[1]):
                    if y == 0 or y == data.shape[0] - 1 or x == 0 or x == data.shape[1] - 1:
                        assert data[y,x]==nd

        # test bad clip
        data=data[:4,:4]
        ds = _generate_mem_raster(data)
        with pytest.raises(ValueError):
            dummy_rastergroup.clip_with_raster(ds)

    def test_calc_max_values(self,dummy_rastergroup):
        maxes=dummy_rastergroup.calc_max_values()
        r1 = dummy_rastergroup['test1'].GetRasterBand(1).ReadAsArray()
        r2 = dummy_rastergroup['test2'].GetRasterBand(1).ReadAsArray()

        for y in range(maxes.shape[0]):
            for x in range(maxes.shape[1]):
                assert max(r1[y,x],r2[y,x])==maxes[y,x]

        # test prefix filter
        maxes= dummy_rastergroup.calc_max_values('test1')
        for y in range(maxes.shape[0]):
            for x in range(maxes.shape[1]):
                assert r1[y, x]== maxes[y, x]

        # check empty results
        assert RasterGroup().calc_max_values() is None

    def test_raster_names_property(self,dummy_rastergroup):
        for n in dummy_rastergroup.raster_names:
            assert n in ('test1','test2')

    def test_empty_raster_names_property(self,dummy_rastergroup):
        # create & add an empty raster
        nodata=-9999.
        data = np.full([dummy_rastergroup.raster_y_size,dummy_rastergroup.raster_x_size],nodata,dtype=np.float32)
        empty_ds = _generate_mem_raster(data,nodata)
        dummy_rastergroup['empty']=empty_ds

        e_names=dummy_rastergroup.empty_raster_names
        assert len(e_names)==1 and e_names[0]=='empty'

    def test_extents_property(self,dummy_rastergroup):
        exts = dummy_rastergroup.extents

        # below only holds true if the geotransform matrix is identity
        assert exts[0]==0 and exts[1]==dummy_rastergroup.raster_x_size and exts[2]==0 \
               and exts[3]==dummy_rastergroup.raster_y_size

        # test empty case
        assert all([x==0 for x in RasterGroup().extents])

    def test_geotransform_property(self,dummy_rastergroup):
        gtrans = dummy_rastergroup.geotransform

        assert len(gtrans)==6 and all([isinstance(i,float) for i in gtrans])

        # test empty case
        assert all([x == 0 for x in RasterGroup().geotransform])


    def test_spatialref_property(self,dummy_rastergroup):

        # see if we can retrieve EPSG for srs
        epsg = int(dummy_rastergroup.spatialref.GetAttrValue("AUTHORITY",1))
        assert _EPSG_CODE==epsg

        # test empty case
        assert RasterGroup().spatialref is None

    def test_raster_y_size_property(self,dummy_rastergroup):
        ySize = dummy_rastergroup.raster_y_size
        assert _DEFAULT_SHAPE[0]==ySize

        # test empty
        assert RasterGroup().raster_y_size==0

    def test_raster_x_size_property(self, dummy_rastergroup):
        xSize = dummy_rastergroup.raster_x_size
        assert _DEFAULT_SHAPE[1] == xSize

        # test empty
        assert RasterGroup().raster_x_size == 0


# def test_list_featureclass_names(dummy_vectors):
#
#     ds = gdal.OpenEx(dummy_vectors[0],gdal.OF_VECTOR)
#     # just grab DA names
#     names=list_featureclass_names(ds,'da*')
#     assert all([x in ('da_1','da_2') for x in names])
#
# def test_list_featureclasses(dummy_vectors):
#     ds = gdal.OpenEx(dummy_vectors[0],gdal.OF_VECTOR)
#     # just grab DA names
#     lyrs=list_featureclasses(ds,'da*')
#     assert all([x.GetName() in ('da_1','da_2') for x in lyrs])

def test_find_unique_components(dummy_vectors):
    ds = gdal.OpenEx(dummy_vectors[0], gdal.OF_VECTOR)
    # just grab DA names
    ucs = find_unique_components(ds, 'da')

    assert all([all([x.GetName() in ('da_1', 'da_2') for x in uc]) for uc in ucs.values()])

# todo: implement tests for:
#   def rasterize_components(src_rasters, gdb_ds, component_data, cache_dir=None, mask=None):
#   def gen_domain_hitmaps(src_rasters):
#   def gen_domain_index_rasters(src_rasters, as_distance, cache_dir=None, mask=None):
#   def find_domain_component_rasters(dom_dist_rasters, hit_maps, test_rasters, cache_dir=None):
#   def combine_domdist_rasters(found, domkey, comp_name, domdist_rasters, combo_rasters, prefix='', suffix='',
#                            drvr_name='mem',opts=None):
#   def norm_multrasters(implicits, explicits, cache_dir=None):
#   def norm_lg_rasters(in_rasters, cache_dir=None):
#   def raster_copy(id, in_ds, drvr_name="mem", prefix='', suffix='',opts=None):
#   def raster_distance(id, in_ds, drvr_name="mem", prefix='', suffix='', mask=None, dist_thresh=None,
#                    gdtype=gdal.GDT_Float32, opts=None):
#   def normalize_raster(in_rast, flip=True):
#   def mult_band_data(data1, data2, id, nd1, nd2, geotrans, spatref, drvr_name='mem', opts=None):
#   def build_pandas_dataframe(index_rasters, data_rasters, index_id='lg', index_df_name='LG_index'):
#   def dataframe_to_rastergroup(df, index_raster, cols=None, gdtype=gdal.GDT_Float32):
