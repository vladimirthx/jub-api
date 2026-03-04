
from pydantic import BaseModel,Field,StringConstraints,field_validator,AfterValidator
from typing import List, Optional,Dict,Annotated
from bson import ObjectId
from enum import Enum


class PyObjectId(ObjectId):
    """Custom ObjectId class to handle BSON ObjectId."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type):
        from pydantic import GetCoreSchemaHandler
        from pydantic_core import core_schema

        # Ensure ObjectId is treated as a string when validating
        return core_schema.with_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)




class LevelCatalog(BaseModel):
    level: int
    cid: str


class Observatory(BaseModel):
    obid:str=""
    title: str="Observatory"
    image_url:str=""
    description:str=""
    catalogs:List[LevelCatalog]=[]
    disabled:bool = False
# x= ""
# x.strip()

class CatalogItem(BaseModel):
    value:str
    display_name:str
    code:int
    description:str
    metadata:Dict[str,str]

    # @field_validator('value', mode='before')




class CatalogKind(str, Enum):
    INTEREST = "INTEREST"
    TEMPORAL = "TEMPORAL"
    SPATIAL  = "SPATIAL"

class Catalog(BaseModel):
    cid:str = ""
    display_name:str = ""
    items: List[CatalogItem] = []
    kind:CatalogKind




class Level(BaseModel):
    index:int
    cid:str
    value:str
    kind:str =""

class Product(BaseModel):
    pid:str=""
    description:str=""
    levels:List[Level]=[]
    product_type: str=""
    level_path:str=""
    profile:str=""
    product_name: str=""
    tags:List[str]=[]
    url:str = ""


# ____________________________________________

# ___________________________________________

# from datetime import datetime
