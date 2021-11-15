from typing import Callable,Optional,Tuple
from osgeo import ogr,gdal,osr
from .common_utils import REE_Workspace
import numpy as np

def ClipLayer(scratchDS:gdal.Dataset,inputLayer:ogr.Layer,clippingLayer:ogr.Layer)->ogr.Layer:
    ...

def IndexCalc(domainType : str, lyr:ogr.Layer) -> gdal.Dataset:
    ...

def indexDomainType(domainType:str,input_DS:gdal.Dataset,lyr:ogr.Layer) -> Tuple[gdal.Dataset,ogr.Layer]:
    ...

def CopyLayer(scratchDS:gdal.Dataset,inPath:str,sRef:Optional[osr.SpatialReference]=None)->ogr.Layer:
    ...

def buildIndices(workspace: REE_Workspace,outputs:REE_Workspace,
                 cellWidth:float,cellHeight:float,sRef:Optional[osr.SpatialReference]) -> Tuple[gdal.Dataset,np.ndarray,np.ndarray]:
    ...

def calcUniqueDomains(inMask:gdal.Dataset,inSD_data:np.ndarray,inLD_data:np.ndarray,outputs:REE_Workspace,nodata:int=...):
    ...

def RunCreatePEGrid(workspace:REE_Workspace,outWorkspace:REE_Workspace,gridWidth:float,gridHeight:float,postProg:Optional[Callable[[int],None]]=None):
    ...