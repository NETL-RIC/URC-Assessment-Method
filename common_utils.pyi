from osgeo import gdal,ogr
from typing import Callable,Dict,Sequence,Generator,Union,Set,Any
import pandas as pd
import numpy as np

class DataPrefix(object):

    def __init__(self,prefix:str): ...
    def __getitem__(self, lbl:str) -> str: ...


class REE_Workspace(object):

    def __init__(self,workspace_dir:str,**kwargs): ...
    def __getitem__(self, item:str)->str: ...
    def __setitem__(self, key:str, value:str): ...
    def __contains__(self,item:str)->bool: ...
    def __iter__(self)->Generator[str,None,None]: ...
    def __dict__(self)->Dict[str,str]: ...
    def __len__(self) -> int: ...
    def DeleteFiles(self,*args,**kwargs): ...

def ParseWorkspaceArgs(vals:Dict[str,str],workspace:REE_Workspace,outputs:REE_Workspace):
    ...

def ListFieldNames(featureclass : ogr.Layer) -> list:
    ...

def FieldValues(lyr : ogr.Layer, field : str) -> list:
    ...

def DeleteFile(path : str,printFn : Callable[...,None] =print):
    ...

def IndexFeatures(outDS:gdal.Dataset,inLyr : ogr.Layer, cellWidth : float,cellHeight : float,addlFields:list=None) -> (gdal.Dataset,ogr.Layer):
    ...


def SpatialJoinCentroid(targetLyr : ogr.Layer, joinLyr : ogr.Layer, outDS : gdal.Dataset) -> ogr.Layer:
    ...

def CreateCopy(inDS : gdal.Dataset,path : str,driverName : str) -> gdal.Dataset:
    ...

def WriteIfRequested(inLayer : ogr.Layer, workspace: REE_Workspace, tag : str, drvrName : str = 'ESRI Shapefile', printFn : Callable[..., None] =print):
    ...

def OgrPandasJoin(inLyr : ogr.Layer, inField : str, joinDF : pd.DataFrame, joinField : str,copyFields : list = None):
    ...

def BuildLookups(lyr : ogr.Layer,indFields : Sequence[str])-> Dict[str,int]:
    ...

def MarkIntersectingFeatures(testLyr : ogr.Layer,filtLyr : ogr.Layer,domInds:Dict[str,int],fcInd:int,hitMatrix:np.array,printFn : Callable[...,None] =print):
    ...

def GetFilteredFeatures(inlyr : ogr.Layer,filterLyr : ogr.Layer):
    ...

def CopyFilteredFeatures(inlyr : ogr.Layer,filterLyr : ogr.Layer,dsOrLyr : Union[gdal.Dataset,ogr.Layer]) -> ogr.Layer:
    ...

def GetFilteredUniqueValues(inlyr : ogr.Layer,filterLyr : ogr.Layer,field : Union[str,int]) -> Set[Any]:
    ...