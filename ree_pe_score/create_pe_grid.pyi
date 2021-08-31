from typing import Callable,Optional,Tuple
from osgeo import ogr,gdal,osr
from .common_utils import REE_Workspace
import numpy as np

def IndexCalc(domainType : str, domainDS : gdal.Dataset) -> gdal.Dataset:
    ...

def indexDomainType(domainType:str,input_file:str,layerInd:int=0) -> gdal.Dataset:
    ...

def buildIndices(ds : gdal.Dataset,workspace: REE_Workspace,outputs:REE_Workspace,
                 cellWidth:float,cellHeight:float) -> Tuple[gdal.Dataset,np.ndarray,np.ndarray]:
    ...

def calcUniqueDomains(inMask:gdal.Dataset,inSD_data:np.ndarray,inLD_data:np.ndarray,outputs:REE_Workspace,nodata:int):
    ...

def RunCreatePEGrid(workspace:REE_Workspace,output_dir:REE_Workspace,gridWidth:float,gridHeight:float,postProg:Optional[Callable[[int],None]]=None):
    ...