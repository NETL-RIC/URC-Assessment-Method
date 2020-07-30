from osgeo import ogr,gdal
from common_utils import PE_Workspace


def IndexCalc(domainType : str, domain_shp : gdal.Dataset) -> gdal.Dataset:
    ...

def indexDomainType(domainType:str,input_file:str,) -> gdal.Dataset:
    ...

def ClearPEDatasets(paths:PE_Workspace):
    ...

def buildIndices(ds : gdal.Dataset,workspace: PE_Workspace,outputs:PE_Workspace,
                 polygonWidth:float,polygonHeight:float) -> ogr.Layer:
    ...

def calcUniqueDomains(inDS : gdal.Dataset,grid_LG_SD_LD : ogr.Layer,outputs : PE_Workspace) -> ogr.Layer:
    ...

def copyPE_Grid(workingDS:gdal.Dataset,PE_Grid_calc:ogr.Layer) -> ogr.Layer:
    ...