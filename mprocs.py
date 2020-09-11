import multiprocessing as mp
from osgeo import ogr

def initTestGeom(testGeomStr,geomStrs):

    global gGeoms
    global gTestGeom

    gGeoms = [ogr.CreateGeometryFromWkt(g) for g in geomStrs]
    gTestGeomStr= ogr.CreateGeometryFromWkt(testGeomStr)

def testGeom(id,testGeom):

    return 1 if testGeom.Intersects(gGeoms[id]) else 0

def testIntersects(feat,geomStrs):


    workPool = mp.Pool(initializer=initTestGeom,initargs=(feat.GetGeometryRef().ExportToWkt(),geomStrs))