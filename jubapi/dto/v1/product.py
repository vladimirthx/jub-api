from pydantic import BaseModel,Field
from jubapi.models import CatalogKind
from typing import List,Optional

class LevelDTO(BaseModel):
    index:int
    cid:str
    value:str
    kind:CatalogKind
    
class ProductDTO(BaseModel):
    pid:str = Field(...,description="Unique identifier for the product")
    description:Optional[str]=Field("",description="Description of the product")
    product_type:str = Field(...,description="Type of the product")    
    level_path:str = Field(...,description="Path of the product levels")  
    levels:List[LevelDTO] = Field(...,description="List of levels for the product")
    profile:str = Field(...,description="Profile of the product")     
    product_name:str = Field(...,description="Name of the product")
    url:str = Field(...,description="URL of the product")
    tags:Optional[List[str]]=Field([],description="Tags associated with the product")