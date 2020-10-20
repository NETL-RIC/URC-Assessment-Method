import sys
from osgeo import gdal,ogr
import pandas
from typing import Tuple,List,Union,Dict,Callable,Optional,Protocol,Any
from .common_utils import REE_Workspace

class PrintFn(Protocol):
    def __call__(self,*args:Any,sep:str=' ',end:str='\n'):
        ...

cpes_print:PrintFn

def printTimeStamp(rawSeconds:Union[int,float]):
    ...

def ListFeatureClassNames(ds:gdal.Dataset,wildCard:str,first_char:int=0, last_char:int=sys.maxsize) ->List[str]:
    ...

def ListFeatureClasses(ds:gdal.Dataset,wildCard:str) ->List[ogr.Layer]:
    ...

def replaceNULL(feature_class : ogr.Layer, field : str):
    ...

def FindUniqueComponents(gdbDS : gdal.Dataset,prefix : str) -> Tuple[List[str],List[List[ogr.Layer]]]:
    ...

def FeaturesPresent(PE_Grid :ogr.Layer, unique_components : List[str], components_data_array : List[List[ogr.Layer]], scratchDS : gdal.Dataset, outputs : REE_Workspace) -> ogr.Layer:
    ...

def DetermineDataForComponents(PE_Grid : ogr.Layer, unique_components : List[str]) -> ogr.Layer:
    ...

def DistribOverDomains(PE_Grid : ogr.Layer, unique_components:List[str]) -> Dict[str,pandas.DataFrame]:
    ...

def CalcSum(df_dict_LG_domains_ALL : Dict[str,pandas.DataFrame], inFeatures : ogr.Layer, prefix : str, outputs : REE_Workspace):
    ...

def RunPEScoreCalc(gdbPath : str,targetData : str,inWorkspace : REE_Workspace,outWorkspace : REE_Workspace,printFn:Optional[PrintFn]=None,postProg:Optional[Callable[[int],None]]=None):
    ...