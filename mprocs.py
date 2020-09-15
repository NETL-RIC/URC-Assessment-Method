import multiprocessing as mp
from osgeo import ogr,osr,gdal

def initTestGeom(testGeomStr,geomStrs):

    # global gGeoms
    # global gTestGeom
    #
    # gGeoms = [ogr.CreateGeometryFromWkt(g) for g in geomStrs]
    # gTestGeomStr= ogr.CreateGeometryFromWkt(testGeomStr)

    global gScratchDS
    gScratchDS = gdal.GetDriverByName('memory').Create('scratch',0,0,0,gdal.OF_VECTOR)

def testGeom(id,testGeom):

    return 1 if testGeom.Intersects(gGeoms[id]) else 0

def testIntersects(feat,geomStrs):


    workPool = mp.Pool(initializer=initTestGeom,initargs=(feat.GetGeometryRef().ExportToWkt(),geomStrs))


def MarkIntersectingFeatures(testLyr,filtLyr,scratchDS,printFn=print):

    scratchLyr = scratchDS.CreateLayer("MarkIntersectingFeatures_scratch",testLyr.GetSpatialRef())

    # cache field index
    idx = testLyr.GetLayerDefn().GetFieldIndex(filtLyr.GetName())
    coordTrans = osr.CoordinateTransformation(filtLyr.GetSpatialRef(), testLyr.GetSpatialRef())
    # transform filter coords

    if testLyr.GetSpatialRef().IsSame(filtLyr.GetSpatialRef())==0:
        # we need to reproject
        printFn("   Reprojecting...", end=' ')
        projLyr = scratchDS.CreateLayer("MarkIntersectingFeatures_reproj",testLyr.GetSpatialRef())

        # we can ignore attributes since we are just looking at geometry
        for feat in filtLyr:
            geom = feat.GetGeometryRef()
            geom.Transform(coordTrans)
            tFeat=ogr.Feature(projLyr.GetLayerDefn())
            tFeat.SetGeometry(geom)
            projLyr.CreateFeature(tFeat)

        filtLyr=projLyr
        printFn("Done")
    else:
        printFn("   Spatial Reference match")


    printFn("   Clipping...",end=' ')
    testLyr.Intersection(filtLyr,scratchLyr) #,["PROMOTE_TO_MULTI=YES"])
    printFn("Done")

    # mark the appropiate fields in global list
    ...

    scratchDS.DeleteLayer("MarkIntersectingFeatures_scratch")
    scratchDS.DeleteLayer("MarkIntersectingFeatures_reproj")