import os
import sys
from time import sleep
import pytest

from urclib.common_utils import *

@pytest.fixture(scope="session")
def geo_test_dir(tmp_path_factory):
    geo_path = tmp_path_factory.mktemp('data')

    # add file to test for deletion
    drvr = gdal.GetDriverByName("ESRI Shapefile")
    ds = drvr.Create(os.path.join(geo_path,'testShp.shp'),0,0,0,gdal.OF_VECTOR)

    testLyr=ds.CreateLayer("test_layer")
    testLyr.CreateField(ogr.FieldDefn('test1',ogr.OFTReal))
    testLyr.CreateField(ogr.FieldDefn('test2', ogr.OFTInteger))

    # create any temp files here
    return geo_path

@pytest.fixture(scope="session")
def geo_test_data():

    prj = osr.SpatialReference()
    prj.ImportFromEPSG(3857)

    drvr = gdal.GetDriverByName("MEMORY")
    vec_ds = drvr.Create('test_vec', 0, 0, 0, gdal.OF_VECTOR)

    testLyr = vec_ds.CreateLayer("test_layer",prj)
    testLyr.CreateField(ogr.FieldDefn('test1', ogr.OFTReal))
    testLyr.CreateField(ogr.FieldDefn('test2', ogr.OFTInteger))

    # add basic geometry to test intersects
    feat = ogr.Feature(testLyr.GetLayerDefn())
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint( 5, 5)
    ring.AddPoint( 5,10)
    ring.AddPoint(10,10)
    ring.AddPoint(10, 5)
    ring.AddPoint( 5, 5)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    feat.SetGeometry(poly)
    feat.SetField(0,0.5)
    feat.SetField(1,2)
    testLyr.CreateFeature(feat)


    # add raster for testing intersects
    drvr = gdal.GetDriverByName('MEM')
    rast_ds = drvr.Create('test_rast',20,20,1,gdal.GDT_Float32)
    b = rast_ds.GetRasterBand(1)
    data = np.ones([20,20],dtype=np.float32)
    b.WriteArray(data)

    # create any temp files here
    return {'test_vec':vec_ds,
            'test_rast':rast_ds}


@pytest.fixture(scope="session")
def urc_data(tmp_path_factory):
    return tmp_path_factory.mktemp("urcData")

@pytest.fixture(scope="session")
def example_urc_workspace(urc_data):
    with open(urc_data/ 'tmp1.txt','w') as t1out:
        t1out.write('this should be used for absolute')
    with open(urc_data / 'tmp2.txt','w') as t2out:
        t2out.write('this should be used for relative')

    return UrcWorkspace(urc_data,absolute=urc_data/'tmp1.txt',relative='tmp2.txt',missing='tmp3.txt')

@pytest.fixture(scope="function")
def virtual_urc_workspace():

    # no file backing
    return UrcWorkspace('/base',t1='file1.txt',t2='file2.txt')

class TestUrcWorkspace(object):

    def test_default_construct(self):
        workspace=UrcWorkspace()
        assert workspace.workspace == '.' and len(workspace) == 0

    def test_workspace_construct(self):
        workspace=UrcWorkspace('some/place')
        assert workspace.workspace is not None and len(workspace) == 0

    def test_kwargs(self):
        workspace=UrcWorkspace(a='a.txt',b='b.txt')
        assert workspace.workspace == '.' and len(workspace) == 2

    def test_workspace_kwargs(self):
        workspace=UrcWorkspace('some/place',a='a.txt',b='b.txt')
        assert workspace.workspace is not None and len(workspace) == 2

    def test_getter(self,example_urc_workspace):
        with pytest.raises(KeyError):
            example_urc_workspace['no_entry']
        example_urc_workspace['relative']

    def test_setter(self):
        workspace = UrcWorkspace()
        with pytest.raises(ValueError):
            workspace['another'] = 4.5
        workspace['another']='fake_path'

    def test___iter__(self,virtual_urc_workspace):

        if sys.platform == 'win32':
            for p in virtual_urc_workspace:
                assert p[2:] in ('/base/file1.txt','/base/file2.txt')
        else:
            for p in virtual_urc_workspace:
                assert p in ('/base/file1.txt','/base/file2.txt')

    def test___delitem__(self,virtual_urc_workspace):

        del virtual_urc_workspace['t1']
        assert 't1' not in virtual_urc_workspace

    def test_update(self,virtual_urc_workspace):

        virtual_urc_workspace.update({'t3': 'newFile.txt'})
        assert 't3' in virtual_urc_workspace

    def test_contains(self,example_urc_workspace):
        assert 'absolute' in example_urc_workspace
        assert 'nothing' not in example_urc_workspace

    def test___repr__(self,virtual_urc_workspace):
        rep = virtual_urc_workspace.__repr__()

        assert rep=='Root:"/base" Tags: {\'t1\': \'file1.txt\', \'t2\': \'file2.txt\'}'

    def test_keys(self,virtual_urc_workspace):
        for k in virtual_urc_workspace.keys():
            assert k in ('t1','t2')


    def test_get(self,virtual_urc_workspace):

        # test included
        assert virtual_urc_workspace.get('t1').endswith('file1.txt')
        # test excluded
        assert virtual_urc_workspace.get('t3','nofile.txt')=='nofile.txt'

    def test_test_files_exist(self,example_urc_workspace):
        for key, found in (example_urc_workspace.test_files_exist()):
            if key == 'missing':
                assert found== False
            else:
                assert found == True

    def test_delete_files(self,geo_test_dir):

        ws=UrcWorkspace(geo_test_dir,test1='td1.txt',test2='td2.txt')
        with open(ws['test1'],'w') as in1, open(ws['test2'],'w') as in2:
            in1.write('Hi\n')
            in2.write('There\n')

        testFiles=(ws['test1'],ws['test2'])
        assert all([os.path.exists(t) for t in testFiles])
        ws.delete_files('test1','test2')

        assert all([not os.path.exists(t) for t in testFiles])

    def test_exists(self,example_urc_workspace):
        assert example_urc_workspace.exists('absolute')==True
        assert example_urc_workspace.exists('relative')==True
        assert example_urc_workspace.exists('missing')==False


def test_do_time_capture_context():

    with do_time_capture():
        sleep(2)

def test_parse_workspace_args():
    vals={'IN_t1':'t1.txt','OUT_t2':'t2.txt','t3':'t3.txt'}
    inWorkspace=UrcWorkspace()
    outWorkspace=UrcWorkspace()
    parse_workspace_args(vals,inWorkspace,outWorkspace)

    assert 't1' in inWorkspace and 't1' not in outWorkspace
    assert 't2' not in inWorkspace and 't2' in outWorkspace
    assert 't3' not in inWorkspace and 't3' not in outWorkspace

def test_list_fieldnames(geo_test_dir):

    ds=gdal.OpenEx(os.path.join(geo_test_dir,'testShp.shp'),gdal.OF_VECTOR)
    names= list_fieldnames(ds.GetLayer(0))

    assert names[0]=='test1' and names[1]=='test2'

def test_delete_file(geo_test_dir):
    path=os.path.join(geo_test_dir, 'testShp.shp')
    assert os.path.exists(path)
    delete_file(path)
    assert not os.path.exists(path)

def test_index_feats_and_raster_domain_intersect(geo_test_data):


    lyr = geo_test_data['test_vec'].GetLayer(0)
    rMask=geo_test_data['test_rast']
    coord_map,i_ds = index_features(lyr,1,1)

    assert coord_map is not None and i_ds is not None

    vals= raster_domain_intersect(coord_map,rMask.GetRasterBand(1).ReadAsArray().ravel(),lyr.GetSpatialRef(),lyr,'test1')
    assert any([i==-9999 for i in vals.ravel()])

def test_rasterize(geo_test_data):

    layers= [geo_test_data['test_vec'].GetLayer(i) for i in range(geo_test_data['test_vec'].GetLayerCount())]
    result = rasterize('rasterized',layers,geo_test_data['test_vec'],20,20,geo_test_data['test_rast'].GetGeoTransform(),layers[0].GetSpatialRef())

    # test something about the raster
    assert result.RasterYSize==20 and result.RasterXSize==20


def test_write_raster(geo_test_dir,geo_test_data):

    data = np.ones([20,20],dtype=np.float32)
    ds = write_raster(geo_test_data['test_rast'],data,os.path.join(geo_test_dir,'new_raster.tif'))

    assert ds.RasterXSize==20 and ds.RasterYSize==20